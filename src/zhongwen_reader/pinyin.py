"""Convert CC-CEDICT numbered pinyin (zhong1, lu:4) to accented form with tones."""

from __future__ import annotations

_TONE_MARKS = {
    "a": "āáǎàa",
    "e": "ēéěèe",
    "i": "īíǐìi",
    "o": "ōóǒòo",
    "u": "ūúǔùu",
    "ü": "ǖǘǚǜü",
    "A": "ĀÁǍÀA",
    "E": "ĒÉĚÈE",
    "I": "ĪÍǏÌI",
    "O": "ŌÓǑÒO",
    "U": "ŪÚǓÙU",
    "Ü": "ǕǗǙǛÜ",
}

_VOWELS = set("aeiouüAEIOUÜ")


def syllable_tone(syllable: str) -> int:
    """Tone number of a numbered-pinyin syllable; 5 (neutral) if unmarked."""
    if syllable and syllable[-1] in "12345":
        return int(syllable[-1])
    return 5


def accent_syllable(syllable: str) -> str:
    """Convert e.g. 'zhong1' -> 'zhōng', 'lu:4' -> 'lǜ', 'ma5' -> 'ma'."""
    tone = syllable_tone(syllable)
    body = syllable[:-1] if syllable and syllable[-1] in "12345" else syllable
    body = body.replace("u:", "ü").replace("U:", "Ü")
    if tone == 5:
        return body

    # Tone mark goes on a/e if present, on o of "ou", else the last vowel.
    mark_pos = -1
    for i, ch in enumerate(body):
        if ch in "aeAE":
            mark_pos = i
            break
    if mark_pos == -1:
        ou = body.lower().find("ou")
        if ou != -1:
            mark_pos = ou
    if mark_pos == -1:
        for i in range(len(body) - 1, -1, -1):
            if body[i] in _VOWELS:
                mark_pos = i
                break
    if mark_pos == -1:
        return body

    marked = _TONE_MARKS[body[mark_pos]][tone - 1]
    return body[:mark_pos] + marked + body[mark_pos + 1 :]


def format_pinyin(pinyin: str) -> list[tuple[str, int]]:
    """Split a CC-CEDICT pinyin string into (accented syllable, tone) pairs."""
    return [(accent_syllable(s), syllable_tone(s)) for s in pinyin.split()]
