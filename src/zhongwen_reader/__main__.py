"""Zhongwen Reader: hold the trigger key and hover over Chinese or Japanese text."""

from __future__ import annotations

import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .capture import capture_around, enable_dpi_awareness, get_cursor_pos
from .config import load_config, save_language, write_default_config
from .hotkey import is_key_held
from .ocr import ChineseOcr, text_at_point
from .popup import Popup
from .providers import get_provider
from .tray import start_tray

POLL_HELD_S = 0.03
POLL_IDLE_S = 0.05
MOVE_THRESHOLD_PX = 4

LANGUAGE_PACK_HELP = """\
No {lang} OCR language pack is installed, so on-screen text cannot be read.

To install (one time only):

1. Open Settings > Time & Language > Language & region
2. Add a language: {packs}
3. You can untick everything except the basic pack. Windows adds
   the OCR component automatically.
4. Restart Zhongwen Reader.

(You do not need to change your display or keyboard language.)"""

PACK_NAMES = {
    "chinese": '"中文(中华人民共和国)" for simplified, "中文(台湾)" for traditional',
    "japanese": '"日本語"',
}


def data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "data"
    return Path(__file__).resolve().parents[2] / "data"


def worker(
    stop: threading.Event,
    paused: threading.Event,
    results: queue.Queue,
    state: dict,
    ocr: ChineseOcr,
    trigger_vk: int,
    max_word_length: int,
) -> None:
    last_pos: tuple[int, int] | None = None
    showing = False
    while not stop.is_set():
        if paused.is_set() or not is_key_held(trigger_vk):
            if showing:
                results.put(("hide",))
                showing = False
            last_pos = None
            time.sleep(POLL_IDLE_S)
            continue

        x, y = get_cursor_pos()
        if last_pos and (
            abs(x - last_pos[0]) < MOVE_THRESHOLD_PX
            and abs(y - last_pos[1]) < MOVE_THRESHOLD_PX
        ):
            time.sleep(POLL_HELD_S)
            continue
        last_pos = (x, y)

        provider = state["provider"]
        cap = capture_around(x, y)
        ix, iy = cap.to_image_coords(x, y)
        segments = []
        for script in provider.ocr_scripts:
            if script not in ocr.available_scripts:
                continue
            text = text_at_point(
                ocr.recognize(cap.image, script),
                ix,
                iy,
                max_word_length,
                is_word_char=provider.is_word_char,
            )
            if text:
                segments = provider.lookup(text)
                if segments:
                    break

        if segments:
            results.put(("show", segments, x, y))
            showing = True
        elif showing:
            results.put(("hide",))
            showing = False


def main() -> None:
    enable_dpi_awareness()
    config = load_config()
    write_default_config()

    root = tk.Tk()
    root.withdraw()

    ocr = ChineseOcr()
    state = {"provider": get_provider(config.language, data_dir())}

    def check_ocr_pack(language: str) -> bool:
        provider_scripts = {
            "chinese": ["Hans", "Hant"],
            "japanese": ["Ja"],
        }[language]
        if any(s in ocr.available_scripts for s in provider_scripts):
            return True
        messagebox.showwarning(
            "Zhongwen Reader — OCR pack needed",
            LANGUAGE_PACK_HELP.format(
                lang=language.capitalize(), packs=PACK_NAMES[language]
            ),
        )
        return False

    if not check_ocr_pack(config.language) and not ocr.available_scripts:
        sys.exit(1)

    popup = Popup(root, font_size=config.font_size)

    stop = threading.Event()
    paused = threading.Event()
    results: queue.Queue = queue.Queue()

    threading.Thread(
        target=worker,
        args=(stop, paused, results, state, ocr,
              config.trigger_vk, config.max_word_length),
        daemon=True,
    ).start()

    def on_quit():
        stop.set()
        root.after(0, root.destroy)

    def on_language(language: str):
        state["provider"] = get_provider(language, data_dir())
        save_language(language)
        check_ocr_pack(language)

    start_tray(
        paused,
        on_quit,
        on_language=on_language,
        current_language=lambda: state["provider"].name,
    )

    def poll_results():
        try:
            msg = None
            while True:
                msg = results.get_nowait()
        except queue.Empty:
            pass
        if msg:
            if msg[0] == "show":
                _, segments, x, y = msg
                popup.show(segments, x, y)
            else:
                popup.hide()
        root.after(30, poll_results)

    poll_results()
    root.mainloop()


if __name__ == "__main__":
    main()
