"""Japanese: JMdict lookup with rule-based deinflection and kana readings."""

from __future__ import annotations

from pathlib import Path

from ..deinflect import deinflect
from ..jmdict import JEntry, JMdict

MAX_MATCHES = 4

Segment = tuple[str, str, int | None]


def _is_japanese_char(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x4E00 <= cp <= 0x9FFF  # kanji
        or 0x3400 <= cp <= 0x4DBF
        or 0xF900 <= cp <= 0xFAFF
        or 0x3041 <= cp <= 0x309F  # hiragana
        or 0x30A0 <= cp <= 0x30FF  # katakana (incl. ー)
        or cp == 0x3005  # 々 iteration mark
    )


def _entry_segments(word: str, entry: JEntry, reasons: tuple[str, ...]) -> list[Segment]:
    segments: list[Segment] = [("hanzi", word, None)]
    if entry.kanji and word not in entry.kanji:
        segments.append(("hanzi_alt", f"（{entry.kanji[0]}）", None))
    for reading in entry.readings[:2]:
        if reading != word:
            segments.append(("reading", reading, None))
    if reasons:
        segments.append(("inflection", "← " + " ← ".join(reasons), None))
    if len(entry.senses) > 1:
        text = "  ".join(f"{i}. {s}" for i, s in enumerate(entry.senses, 1))
    else:
        text = entry.senses[0]
    segments.append(("definition", text, None))
    return segments


class JapaneseProvider:
    name = "japanese"
    display_name = "日本語"
    ocr_scripts = ["Ja"]

    def __init__(self, data_dir: Path):
        self._dictionary = JMdict.load(data_dir / "jmdict_e.tsv.gz")

    def is_word_char(self, ch: str) -> bool:
        return _is_japanese_char(ch)

    def lookup(self, text: str) -> list[Segment]:
        segments: list[Segment] = []
        shown = 0
        seen: set[tuple[str, int]] = set()
        for length in range(len(text), 0, -1):
            if shown >= MAX_MATCHES:
                break
            surface = text[:length]
            for cand in deinflect(surface):
                entries = self._dictionary.lookup(cand.word)
                if cand.pos_filter is not None:
                    entries = [e for e in entries if e.pos & cand.pos_filter]
                for entry in entries:
                    key = (cand.word, id(entry))
                    if key in seen:
                        continue
                    seen.add(key)
                    if shown >= MAX_MATCHES:
                        break
                    if segments:
                        segments.append(("separator", "", None))
                    segments.extend(_entry_segments(cand.word, entry, cand.reasons))
                    shown += 1
        return segments
