"""Language providers: everything language-specific behind one interface.

A provider exposes:
- name: str
- display_name: str          (tray menu label)
- ocr_scripts: list[str]     (OCR engine preference order)
- is_word_char(ch) -> bool   (characters the cursor mapping accepts)
- lookup(text) -> list[Segment]  (popup segments for text starting at cursor)
"""

from __future__ import annotations

from pathlib import Path


def get_provider(name: str, data_dir: str | Path):
    data_dir = Path(data_dir)
    if name == "chinese":
        from .chinese import ChineseProvider

        return ChineseProvider(data_dir)
    if name == "japanese":
        from .japanese import JapaneseProvider

        return JapaneseProvider(data_dir)
    raise ValueError(f"unknown language provider: {name!r}")
