"""Chinese: CC-CEDICT longest-match lookup with tone-colored pinyin."""

from __future__ import annotations

from pathlib import Path

from ..dictionary import Dictionary, Match
from ..ocr import is_cjk
from ..pinyin import format_pinyin

MAX_MATCHES = 4

# (kind, text, tone) — kinds: hanzi, hanzi_alt, pinyin, definition, separator
Segment = tuple[str, str, int | None]


def build_segments(matches: list[Match]) -> list[Segment]:
    """Flatten dictionary matches into (kind, text, tone) render segments."""
    segments: list[Segment] = []
    for i, match in enumerate(matches[:MAX_MATCHES]):
        if i:
            segments.append(("separator", "", None))
        for entry in match.entries:
            shown = match.word
            alt = entry.traditional if shown == entry.simplified else entry.simplified
            segments.append(("hanzi", shown, None))
            if alt != shown:
                segments.append(("hanzi_alt", f"（{alt}）", None))
            for syllable, tone in format_pinyin(entry.pinyin):
                segments.append(("pinyin", syllable, tone))
            segments.append(("definition", "; ".join(entry.definitions), None))
    return segments


class ChineseProvider:
    name = "chinese"
    display_name = "中文"
    ocr_scripts = ["Hans", "Hant"]

    def __init__(self, data_dir: Path):
        self._dictionary = Dictionary.load(data_dir / "cedict_ts.u8")

    def is_word_char(self, ch: str) -> bool:
        return is_cjk(ch)

    def lookup(self, text: str) -> list[Segment]:
        return build_segments(self._dictionary.match_prefixes(text))
