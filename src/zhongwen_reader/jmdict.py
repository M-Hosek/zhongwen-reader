"""JMdict: build-time XML → compact TSV conversion and runtime loading.

TSV columns (tab-separated, gzipped):
    kanji forms "|"-joined | kana readings "|"-joined |
    POS codes ","-joined | senses "\\"-joined (glosses "; "-joined per sense)
"""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

# JMdict marks POS etc. with DTD entities (&v1; &n; ...). We want the short
# codes, so strip the & and ; before parsing instead of expanding the DTD.
_ENTITY_RE = re.compile(r"&(?!amp;|lt;|gt;|quot;|apos;)([\w-]+);")


@dataclass(frozen=True)
class JEntry:
    kanji: list[str]
    readings: list[str]
    pos: frozenset[str]
    senses: list[str]


def convert_xml(xml_path: str | Path, out_path: str | Path) -> int:
    """Convert JMdict_e XML to the compact TSV format; returns entry count."""
    text = Path(xml_path).read_text(encoding="utf-8")
    text = _ENTITY_RE.sub(r"\1", text)
    count = 0
    with gzip.open(out_path, "wt", encoding="utf-8") as out:
        root = ElementTree.fromstring(text)
        for entry in root.iter("entry"):
            kanji = [k.text for k in entry.iter("keb")]
            readings = [r.text for r in entry.iter("reb")]
            pos = sorted({p.text for p in entry.iter("pos")})
            senses = []
            for sense in entry.iter("sense"):
                glosses = [g.text for g in sense.iter("gloss") if g.text]
                if glosses:
                    senses.append("; ".join(glosses))
            if not (readings and senses):
                continue
            out.write(
                "\t".join(
                    [
                        "|".join(kanji),
                        "|".join(readings),
                        ",".join(pos),
                        "\\".join(senses),
                    ]
                )
                + "\n"
            )
            count += 1
    return count


def parse_tsv_line(line: str) -> JEntry:
    kanji, readings, pos, senses = line.rstrip("\n").split("\t")
    return JEntry(
        kanji=kanji.split("|") if kanji else [],
        readings=readings.split("|") if readings else [],
        pos=frozenset(pos.split(",")) if pos else frozenset(),
        senses=senses.split("\\"),
    )


class JMdict:
    def __init__(self, index: dict[str, list[JEntry]]):
        self._index = index

    @classmethod
    def load(cls, path: str | Path) -> "JMdict":
        index: dict[str, list[JEntry]] = {}
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = parse_tsv_line(line)
                for key in entry.kanji + entry.readings:
                    index.setdefault(key, []).append(entry)
        return cls(index)

    def lookup(self, word: str) -> list[JEntry]:
        return self._index.get(word, [])
