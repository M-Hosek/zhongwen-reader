"""CC-CEDICT parsing and longest-match word lookup."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Longest headword worth trying when matching text under the cursor.
MAX_WORD_LENGTH = 8

_LINE_RE = re.compile(r"^(\S+) (\S+) \[([^\]]*)\] /(.+)/\s*$")


@dataclass(frozen=True)
class Entry:
    traditional: str
    simplified: str
    pinyin: str
    definitions: list[str]

    def __eq__(self, other):
        if not isinstance(other, Entry):
            return NotImplemented
        return (
            self.traditional == other.traditional
            and self.simplified == other.simplified
            and self.pinyin == other.pinyin
            and self.definitions == other.definitions
        )

    def __hash__(self):
        return hash((self.traditional, self.simplified, self.pinyin))


@dataclass(frozen=True)
class Match:
    word: str
    entries: list[Entry]


def parse_cedict_line(line: str) -> Entry | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = _LINE_RE.match(line)
    if not m:
        return None
    traditional, simplified, pinyin, defs = m.groups()
    return Entry(
        traditional=traditional,
        simplified=simplified,
        pinyin=pinyin,
        definitions=defs.split("/"),
    )


class Dictionary:
    def __init__(self, index: dict[str, list[Entry]]):
        self._index = index

    @classmethod
    def load(cls, path: str | Path) -> "Dictionary":
        index: dict[str, list[Entry]] = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                entry = parse_cedict_line(line)
                if entry is None:
                    continue
                index.setdefault(entry.simplified, []).append(entry)
                if entry.traditional != entry.simplified:
                    index.setdefault(entry.traditional, []).append(entry)
        return cls(index)

    def lookup(self, word: str) -> list[Entry]:
        return self._index.get(word, [])

    def match_prefixes(self, text: str) -> list[Match]:
        """All dictionary words that are prefixes of `text`, longest first."""
        matches = []
        for length in range(min(len(text), MAX_WORD_LENGTH), 0, -1):
            word = text[:length]
            entries = self.lookup(word)
            if entries:
                matches.append(Match(word=word, entries=entries))
        return matches
