"""Integration test: render Chinese text to an image and run real Windows OCR.

Skipped automatically if the zh-Hans OCR language pack is not installed.
"""

import pytest
from PIL import Image, ImageDraw, ImageFont

from zhongwen_reader.ocr import ChineseOcr, text_at_point

ocr = ChineseOcr()

pytestmark = pytest.mark.skipif(
    "Hans" not in ocr.available_scripts, reason="zh-Hans OCR pack not installed"
)


def render(text, font_size=32):
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", font_size)
    img = Image.new("RGB", (60 + font_size * len(text), font_size * 3), "white")
    ImageDraw.Draw(img).text((30, font_size), text, font=font, fill="black")
    return img


def test_recognizes_rendered_chinese():
    lines = ocr.recognize(render("我们的图书馆很大"), "Hans")
    text = "".join(w.text for line in lines for w in line)
    assert "图书馆" in text


def test_text_at_point_on_rendered_image():
    img = render("我们的图书馆很大")
    lines = ocr.recognize(img, "Hans")
    # 图 is the 4th char: x ≈ 30 + 3.5*32, y ≈ mid-text
    tail = text_at_point(lines, 30 + int(3.5 * 32), 48)
    assert tail.startswith("图书馆")
