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


def start_tray(
    paused: threading.Event,
    on_quit,
    on_language=None,
    current_language=None,
) -> pystray.Icon:
    """Run the tray icon on a background thread; returns the icon."""

    def toggle_pause(icon, item):
        if paused.is_set():
            paused.clear()
        else:
            paused.set()

    def quit_app(icon, item):
        icon.stop()
        on_quit()

    def pick_language(language):
        def handler(icon, item):
            on_language(language)
            icon.update_menu()

        return handler

    items = [
        pystray.MenuItem(
            lambda item: "Resume" if paused.is_set() else "Pause",
            toggle_pause,
        ),
    ]
    if on_language is not None:
        items += [
            pystray.MenuItem(
                "中文 (Chinese)",
                pick_language("chinese"),
                checked=lambda item: current_language() == "chinese",
                radio=True,
            ),
            pystray.MenuItem(
                "日本語 (Japanese)",
                pick_language("japanese"),
                checked=lambda item: current_language() == "japanese",
                radio=True,
            ),
        ]
    items.append(pystray.MenuItem("Quit", quit_app))

    icon = pystray.Icon(
        "zhongwen_reader",
        _make_icon_image(),
        "Zhongwen Reader — hold Ctrl and hover over Chinese/Japanese text",
        menu=pystray.Menu(*items),
    )
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
