"""Integration test: render Japanese text and run real Windows OCR.

Skipped automatically if the ja-JP OCR language pack is not installed.
"""

import pytest
from PIL import Image, ImageDraw, ImageFont

from zhongwen_reader.ocr import ChineseOcr, text_at_point
from zhongwen_reader.providers.japanese import _is_japanese_char

ocr = ChineseOcr()

pytestmark = pytest.mark.skipif(
    "Ja" not in ocr.available_scripts, reason="ja-JP OCR pack not installed"
)


def render(text, font_size=32):
    font = ImageFont.truetype(r"C:\Windows\Fonts\msgothic.ttc", font_size)
    img = Image.new("RGB", (60 + font_size * len(text), font_size * 3), "white")
    ImageDraw.Draw(img).text((30, font_size), text, font=font, fill="black")
    return img


def test_recognizes_rendered_japanese():
    lines = ocr.recognize(render("私は図書館で本を食べました"), "Ja")
    text = "".join(w.text for line in lines for w in line)
    assert "図書館" in text
    assert "食べました" in text


def test_text_at_point_with_japanese_predicate():
    img = render("私は図書館で本を読みました")
    lines = ocr.recognize(img, "Ja")
    # 図 is the 3rd char: x ≈ 30 + 2.5*32
    tail = text_at_point(
        lines, 30 + int(2.5 * 32), 48, is_word_char=_is_japanese_char
    )
    assert tail.startswith("図書館")
