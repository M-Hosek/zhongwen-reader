"""User configuration, stored as JSON in %APPDATA%\\ZhongwenReader\\config.json."""

from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass
from pathlib import Path

_VK_CODES = {"ctrl": 0x11, "alt": 0x12, "shift": 0x10}


@dataclass(frozen=True)
class Config:
    trigger_key: str = "ctrl"  # ctrl | alt | shift
    font_size: int = 12
    max_word_length: int = 8
    language: str = "chinese"  # chinese | japanese

    @property
    def trigger_vk(self) -> int:
        return _VK_CODES.get(self.trigger_key, _VK_CODES["ctrl"])


def default_config_path() -> Path:
    return Path(os.environ["APPDATA"]) / "ZhongwenReader" / "config.json"


def load_config(path: str | Path | None = None) -> Config:
    path = Path(path) if path else default_config_path()
    if not path.exists():
        return Config()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Config()
    fields = {f.name for f in dataclasses.fields(Config)}
    return Config(**{k: v for k, v in data.items() if k in fields})


def save_language(language: str, path: str | Path | None = None) -> None:
    """Persist the selected language, preserving other settings in the file."""
    path = Path(path) if path else default_config_path()
    current = load_config(path)
    merged = dataclasses.asdict(dataclasses.replace(current, language=language))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged, indent=2), encoding="utf-8")


def write_default_config(path: str | Path | None = None) -> Path:
    """Create the config file with defaults if it doesn't exist yet."""
    path = Path(path) if path else default_config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(dataclasses.asdict(Config()), indent=2), encoding="utf-8"
        )
    return path
