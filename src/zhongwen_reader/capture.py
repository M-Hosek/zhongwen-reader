"""Screen capture of a strip around the mouse cursor."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass

import mss
from PIL import Image

STRIP_WIDTH = 360
STRIP_HEIGHT = 90
SCALE = 2


def enable_dpi_awareness() -> None:
    """Make the process per-monitor DPI aware so cursor position, tkinter
    geometry, and screen capture all use the same physical pixels.
    Must run before creating any window."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(-4)  # PER_MONITOR_AWARE_V2
        )
    except (AttributeError, OSError):
        ctypes.windll.shcore.SetProcessDpiAwareness(2)


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_cursor_pos() -> tuple[int, int]:
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


@dataclass
class Capture:
    image: Image.Image  # upscaled strip
    origin_x: int  # screen coords of strip's top-left
    origin_y: int
    scale: int

    def to_image_coords(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        return (
            (screen_x - self.origin_x) * self.scale,
            (screen_y - self.origin_y) * self.scale,
        )


def capture_around(
    x: int,
    y: int,
    width: int = STRIP_WIDTH,
    height: int = STRIP_HEIGHT,
    scale: int = SCALE,
) -> Capture:
    """Grab a strip centered on (x, y), upscaled for better OCR accuracy."""
    left = x - width // 2
    top = y - height // 2
    with mss.MSS() as sct:
        raw = sct.grab({"left": left, "top": top, "width": width, "height": height})
    img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    return Capture(image=img, origin_x=left, origin_y=top, scale=scale)
