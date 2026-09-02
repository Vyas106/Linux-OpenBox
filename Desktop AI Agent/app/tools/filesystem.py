"""Filesystem tools for AI agent."""

import os
import shutil
import fnmatch
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..security import SecurityGuard


def _resolve_and_guard(
    path_str: str,
    guard: Optional[SecurityGuard],
    workspace: Optional[Path],
    allow_outside: bool = False,
) -> Path:
    """Helper to resolve path safely within workspace or system."""
    if guard:
        return guard.resolve_path(path_str, allow_outside_workspace=allow_outside)
    base = workspace or Path.cwd()
    p = Path(os.path.expanduser(path_str))
    if not p.is_absolute():
        p = (base / p).resolve()
    else:
        p = p.resolve()
    return p


def list_directory(
    path: str = ".",
    guard: Optional[SecurityGuard] = None,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """List contents of a directory with file types and sizes."""
    try:
        target = _resolve_and_guard(path, guard, workspace, allow_outside=True)
        if not target.exists():
            return {"success": False, "error": f"Directory not found: {path}", "output": None}
        if not target.is_dir():
            return {"success": False, "error": f"Path is not a directory: {path}", "output": None}

        items = []
        for entry in sorted(target.iterdir()):
            is_dir = entry.is_dir()
            size = entry.stat().st_size if not is_dir else 0
            items.append({
                "name": entry.name,
                "type": "directory" if is_dir else "file",
                "size_bytes": size,
            })

        summary = f"Total items: {len(items)}\n"
        for it in items:
            prefix = "[DIR] " if it["type"] == "directory" else "      "
            summary += f"{prefix}{it['name']} ({it['size_bytes']} bytes)\n"

        return {
            "success": True,
            "path": str(target),
            "items": items,
            "output": summary.strip(),
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": None}


def read_file(
    path: str,
    max_lines: int = 500,
    guard: Optional[SecurityGuard] = None,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """Read contents of a text file."""
    try:
        target = _resolve_and_guard(path, guard, workspace, allow_outside=True)
        if not target.exists():
            return {"success": False, "error": f"File not found: {path}", "output": None}
        if not target.is_file():
            return {"success": False, "error": f"Path is a directory, not a file: {path}", "output": None}

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        if total_lines > max_lines:
            content = "".join(lines[:max_lines])
            content += f"\n\n[... Truncated: showing first {max_lines} of {total_lines} lines ...]"
        else:
            content = "".join(lines)

        return {
            "success": True,
            "path": str(target),
            "total_lines": total_lines,
            "output": content,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": None}


def write_file(
    path: str,
    content: str,
    guard: Optional[SecurityGuard] = None,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """Write text content to a file, creating parent directories if needed."""
    try:
        target = _resolve_and_guard(path, guard, workspace)
        target.parent.mkdir(parents=True, exist_ok=True)

        is_new = not target.exists()
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "path": str(target),
            "is_new": is_new,
            "bytes_written": len(content.encode("utf-8")),
            "output": f"Successfully {'created' if is_new else 'updated'} {target.name} ({len(content.splitlines())} lines)",
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": None}


def edit_file(
    path: str,
    old_text: str,
    new_text: str,
    guard: Optional[SecurityGuard] = None,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """Replace an exact substring/block of old_text with new_text in a file."""
    try:
        target = _resolve_and_guard(path, guard, workspace)
        if not target.exists() or not target.is_file():
            return {"success": False, "error": f"File does not exist: {path}", "output": None}

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            original_content = f.read()

        if old_text not in original_content:
            return {
                "success": False,
                "error": f"Target text 'old_text' was not found in {target.name}. Check the file content first.",
                "output": None,
            }

        count = original_content.count(old_text)
        if count > 1:
            return {
                "success": False,
                "error": f"Target 'old_text' found {count} times in {target.name}. Please provide a larger unique block.",
                "output": None,
            }

        new_content = original_content.replace(old_text, new_text, 1)
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Generate diff
        diff = list(
            difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{target.name}",
                tofile=f"b/{target.name}",
                n=3,
            )
        )
        diff_str = "".join(diff)

        return {
            "success": True,
            "path": str(target),
            "diff": diff_str,
            "output": f"Successfully edited {target.name}.\nDiff:\n{diff_str}" if diff_str else f"Successfully edited {target.name}.",
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": None}


def create_directory(
    path: str,
    guard: Optional[SecurityGuard] = None,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """Create directory path recursively."""
    try:
        target = _resolve_and_guard(path, guard, workspace)
        target.mkdir(parents=True, exist_ok=True)
        return {
            "success": True,
            "path": str(target),
            "output": f"Directory created: {target}",
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": None}


def delete_file(
    path: str,
    guard: Optional[SecurityGuard] = None,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """Delete a file or directory inside the workspace."""
    try:
        target = _resolve_and_guard(path, guard, workspace)
        if not target.exists():
            return {"success": False, "error": f"Path does not exist: {path}", "output": None}

        if target.is_dir():
            shutil.rmtree(target)
            return {"success": True, "path": str(target), "output": f"Deleted directory: {target}", "error": None}
        else:
            target.unlink()
            return {"success": True, "path": str(target), "output": f"Deleted file: {target}", "error": None}
    except Exception as e:
        return {"success": False, "error": str(e), "output": None}


def move_file(
    source: str,
    destination: str,
    guard: Optional[SecurityGuard] = None,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """Move or rename a file or directory."""
    try:
        src = _resolve_and_guard(source, guard, workspace)
        dest = _resolve_and_guard(destination, guard, workspace)

        if not src.exists():
            return {"success": False, "error": f"Source does not exist: {source}", "output": None}

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        return {
            "success": True,
            "source": str(src),
            "destination": str(dest),
            "output": f"Moved {src.name} -> {dest}",
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": None}


def search_files(
    path: str = ".",
    pattern: str = "*",
    search_content: bool = False,
    guard: Optional[SecurityGuard] = None,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """Search for files matching name pattern or containing text."""
    try:
        target = _resolve_and_guard(path, guard, workspace, allow_outside=True)
        if not target.exists():
            return {"success": False, "error": f"Path does not exist: {path}", "output": None}

        matches = []
        for root, dirs, files in os.walk(target):
            # Exclude hidden folders like .git
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for file in files:
                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(target))

                if search_content:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            if pattern.lower() in f.read().lower():
                                matches.append(rel_path)
                    except Exception:
                        pass
                else:
                    if fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(rel_path, pattern):
                        matches.append(rel_path)

        return {
            "success": True,
            "matches": matches,
            "output": f"Found {len(matches)} matches:\n" + "\n".join(matches[:50]),
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": None}
