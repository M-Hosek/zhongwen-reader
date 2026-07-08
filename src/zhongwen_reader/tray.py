"""System tray icon with pause/resume and quit."""

from __future__ import annotations

import threading

import pystray
from PIL import Image, ImageDraw, ImageFont


def _make_icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, 62, 62), fill="#c0392b")
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 40)
        draw.text((32, 30), "中", font=font, fill="white", anchor="mm")
    except OSError:
        draw.text((26, 22), "Z", fill="white")
    return img


def start_tray(paused: threading.Event, on_quit) -> pystray.Icon:
    """Run the tray icon on a background thread; returns the icon."""

    def toggle_pause(icon, item):
        if paused.is_set():
            paused.clear()
        else:
            paused.set()

    def quit_app(icon, item):
        icon.stop()
        on_quit()

    icon = pystray.Icon(
        "zhongwen_reader",
        _make_icon_image(),
        "Zhongwen Reader — hold Ctrl and hover over Chinese text",
        menu=pystray.Menu(
            pystray.MenuItem(
                lambda item: "Resume" if paused.is_set() else "Pause",
                toggle_pause,
            ),
            pystray.MenuItem("Quit", quit_app),
        ),
    )
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
