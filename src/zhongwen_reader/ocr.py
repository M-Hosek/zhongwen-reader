"""Windows.Media.Ocr wrapper and cursor-to-character mapping."""

from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass

from PIL import Image
from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

SCRIPT_TAGS = {"Hans": "zh-Hans-CN", "Hant": "zh-Hant-TW"}


@dataclass(frozen=True)
class WordBox:
    text: str
    x: float
    y: float
    w: float
    h: float


def is_cjk(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x4E00 <= cp <= 0x9FFF
        or 0x3400 <= cp <= 0x4DBF
        or 0xF900 <= cp <= 0xFAFF
    )


class ChineseOcr:
    """Offline OCR via the Windows built-in engine, for zh-Hans and zh-Hant."""

    def __init__(self):
        self._engines = {}
        for script, tag in SCRIPT_TAGS.items():
            engine = OcrEngine.try_create_from_language(Language(tag))
            if engine is None:
                # Fall back to the generic tag (pack region may differ)
                engine = OcrEngine.try_create_from_language(
                    Language(f"zh-{script}")
                )
            if engine is not None:
                self._engines[script] = engine

    @property
    def available_scripts(self) -> list[str]:
        return list(self._engines)

    def recognize(self, image: Image.Image, script: str) -> list[list[WordBox]]:
        """OCR a PIL image; returns lines of word boxes in image pixels."""
        engine = self._engines.get(script)
        if engine is None:
            return []
        return asyncio.run(self._recognize_async(engine, image))

    async def _recognize_async(self, engine, image: Image.Image):
        buf = io.BytesIO()
        image.save(buf, format="BMP")
        stream = InMemoryRandomAccessStream()
        writer = DataWriter(stream.get_output_stream_at(0))
        writer.write_bytes(buf.getvalue())
        await writer.store_async()
        await writer.flush_async()
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        lines = []
        for line in result.lines:
            words = []
            for word in line.words:
                r = word.bounding_rect
                words.append(
                    WordBox(text=word.text, x=r.x, y=r.y, w=r.width, h=r.height)
                )
            if words:
                lines.append(words)
        return lines


def _char_boxes(line: list[WordBox]) -> list[tuple[str, float, float]]:
    """Split each word box evenly into (char, x0, x1) spans, left to right."""
    chars = []
    for word in sorted(line, key=lambda w: w.x):
        if not word.text:
            continue
        step = word.w / len(word.text)
        for i, ch in enumerate(word.text):
            chars.append((ch, word.x + i * step, word.x + (i + 1) * step))
    return chars


def text_at_point(
    lines: list[list[WordBox]], px: float, py: float, max_chars: int = 8
) -> str:
    """The run of CJK characters starting under (px, py), reading rightward.

    Returns "" if the point is not over a CJK character.
    """
    line = None
    for candidate in lines:
        top = min(w.y for w in candidate)
        bottom = max(w.y + w.h for w in candidate)
        if top <= py <= bottom:
            line = candidate
            break
    if line is None:
        return ""

    chars = _char_boxes(line)
    start = None
    for i, (ch, x0, x1) in enumerate(chars):
        if x0 <= px < x1:
            start = i
            break
    if start is None or not is_cjk(chars[start][0]):
        return ""

    tail = []
    for ch, _, _ in chars[start:]:
        if not is_cjk(ch) or len(tail) >= max_chars:
            break
        tail.append(ch)
    return "".join(tail)
