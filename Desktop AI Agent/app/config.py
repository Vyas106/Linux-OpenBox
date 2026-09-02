"""Configuration loader and manager for Local AI Agent."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


@dataclass
class AppConfig:
    model: str = "qwen2.5:3b"
    ollama_url: str = "http://localhost:11434"
    workspace: str = "~/AIWorkspace"
    max_tool_calls: int = 30
    window_width: int = 920
    window_height: int = 740
    dark_theme: bool = True
    require_confirmation: bool = True
    auto_approve_safe_commands: bool = True
    temperature: float = 0.2
    context_length: int = 8192

    @property
    def resolved_workspace(self) -> Path:
        """Return expanded and resolved absolute path to workspace."""
        path = Path(os.path.expanduser(self.workspace)).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


def get_config_paths() -> list[Path]:
    """Return prioritized list of potential configuration file paths."""
    paths = []
    # User config dir
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    paths.append(Path(xdg_config_home) / "local-ai-agent" / "config.toml")
    # Current working directory / project dir
    paths.append(Path.cwd() / "config.toml")
    paths.append(Path(__file__).resolve().parent.parent / "config.toml")
    return paths


def load_config(custom_path: Optional[str] = None) -> AppConfig:
    """Load configuration from file or fallback to defaults."""
    config = AppConfig()

    paths_to_try = [Path(custom_path)] if custom_path else get_config_paths()

    for path in paths_to_try:
        if path.exists() and path.is_file():
            try:
                if tomllib is not None:
                    with open(path, "rb") as f:
                        data = tomllib.load(f)
                else:
                    # Minimal manual parser fallback
                    data = {}
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#") or "=" not in line:
                                continue
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if v.isdigit():
                                data[k] = int(v)
                            elif v.lower() in ("true", "false"):
                                data[k] = v.lower() == "true"
                            else:
                                data[k] = v

                for key, val in data.items():
                    if hasattr(config, key):
                        expected_type = type(getattr(config, key))
                        try:
                            setattr(config, key, expected_type(val))
                        except (ValueError, TypeError):
                            setattr(config, key, val)
                break
            except Exception as e:
                print(f"Warning: Failed to load config from {path}: {e}")

    # Ensure workspace directory exists
    try:
        config.resolved_workspace
    except Exception as e:
        print(f"Warning: Could not create workspace directory: {e}")

    return config
