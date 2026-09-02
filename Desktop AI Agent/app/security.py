"""Security and permission guard for commands and filesystem operations."""

import os
import re
import shlex
from pathlib import Path
from typing import Tuple, Optional


class SecurityGuard:
    """Enforces workspace boundaries and command safety policies."""

    # Explicit list of high-risk commands and regex patterns
    DANGEROUS_PATTERNS = [
        (r"\bsudo\b", "Requires root administrative privileges"),
        (r"\bsu\b", "Attempts to switch to root user"),
        (r"\bdoas\b", "Executes commands with elevated privileges"),
        (r"\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+|--recursive\s+|--force\s+)", "Recursive or forced deletion of files/directories"),
        (r"\brm\s+(-r|-f|-rf|-fr)\b", "Forced / recursive deletion"),
        (r"\bmkfs\b", "Disk formatting operation"),
        (r"\bfdisk\b|\bgdisk\b|\bparted\b", "Disk partition manipulation"),
        (r"\bdd\b\s+.*(?:if=|of=)", "Direct raw disk / block device write"),
        (r"\b(?:shutdown|reboot|poweroff|halt|init\s+[06])\b", "System shutdown / reboot command"),
        (r"\bsystemctl\s+(?:stop|disable|mask|restart|poweroff|reboot)\b", "Systemd service control / system power operation"),
        (r"\bchmod\s+(?:-[a-zA-Z]*\s+)?(?:777|000|\+s|u\+s|g\+s|[0-7]{4})\b", "Potentially hazardous permission changes"),
        (r"\bchown\b", "File ownership alteration"),
        (r"\b(?:pacman|yay|paru)\s+-(?:S|R|U|Syu|Syyu)\b", "System package installation/removal"),
        (r"\b(?:apt|apt-get|dnf|zypper|emerge)\b", "System package manager operation"),
        (r"\bcurl\b.*\|\s*(?:ba)?sh\b|\bwget\b.*\|\s*(?:ba)?sh\b", "Remote script piped directly to shell"),
        (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb detected"),
        (r">\s*/dev/(?:sd[a-z]|nvme[0-9]|null|zero|random)", "Direct overwrite of device nodes"),
    ]

    # Critical system paths that should never be written to or deleted without confirmation
    CRITICAL_PATHS = [
        "/etc", "/boot", "/usr", "/bin", "/sbin", "/lib", "/lib64", "/var", "/root", "/dev", "/sys", "/proc"
    ]

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path.resolve()

    def resolve_path(self, raw_path: str, allow_outside_workspace: bool = False) -> Path:
        """
        Resolve a relative or absolute path against the workspace.
        Raises PermissionError if path attempts to traverse outside workspace without permission.
        """
        raw_path = raw_path.strip()
        if raw_path.startswith("~"):
            target = Path(os.path.expanduser(raw_path)).resolve()
        else:
            target_path = Path(raw_path)
            if not target_path.is_absolute():
                target = (self.workspace_path / target_path).resolve()
            else:
                target = target_path.resolve()

        if not allow_outside_workspace:
            # Check if target is inside workspace
            try:
                target.relative_to(self.workspace_path)
            except ValueError:
                raise PermissionError(
                    f"Path '{raw_path}' resolves to '{target}' which is outside the workspace sandbox '{self.workspace_path}'."
                )

        return target

    def is_safe_path(self, raw_path: str) -> Tuple[bool, str]:
        """Check if path is within workspace or safe bounds."""
        try:
            resolved = self.resolve_path(raw_path, allow_outside_workspace=False)
            return True, str(resolved)
        except PermissionError as e:
            return False, str(e)

    def assess_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Analyze a shell command for dangerous operations.
        Returns:
            (is_dangerous: bool, reason: Optional[str])
        """
        cmd_clean = command.strip()
        if not cmd_clean:
            return False, None

        # Check regex patterns
        for pattern, reason in self.DANGEROUS_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return True, reason

        # Check for critical system paths in deletion or redirection
        for crit in self.CRITICAL_PATHS:
            if re.search(rf"\b(?:rm|mv|cp|truncate)\b.*?\s+{re.escape(crit)}(?:/|\s|$)", cmd_clean):
                return True, f"Operation targeting sensitive system directory: {crit}"

        return False, None
