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


def write_default_config(path: str | Path | None = None) -> Path:
    """Create the config file with defaults if it doesn't exist yet."""
    path = Path(path) if path else default_config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(dataclasses.asdict(Config()), indent=2), encoding="utf-8"
        )
    return path
