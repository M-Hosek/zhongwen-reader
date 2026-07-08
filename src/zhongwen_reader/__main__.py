"""Zhongwen Reader: hold the trigger key and hover over Chinese text anywhere."""

from __future__ import annotations

import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .capture import capture_around, enable_dpi_awareness, get_cursor_pos
from .config import load_config, write_default_config
from .dictionary import Dictionary
from .hotkey import is_key_held
from .ocr import ChineseOcr, text_at_point
from .popup import Popup
from .tray import start_tray

POLL_HELD_S = 0.03
POLL_IDLE_S = 0.05
MOVE_THRESHOLD_PX = 4

LANGUAGE_PACK_HELP = """\
No Chinese OCR language pack is installed, so on-screen Chinese cannot be read.

To install (one time only):

1. Open Settings > Time & Language > Language & region
2. Add a language: "中文(中华人民共和国)" for simplified,
   "中文(台湾)" for traditional
3. You can untick everything except the basic pack. Windows adds
   the OCR component automatically.
4. Restart Zhongwen Reader.

(You do not need to change your display or keyboard language.)"""


def data_file(name: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "data" / name
    return Path(__file__).resolve().parents[2] / "data" / name


def worker(
    stop: threading.Event,
    paused: threading.Event,
    results: queue.Queue,
    dictionary: Dictionary,
    ocr: ChineseOcr,
    trigger_vk: int,
    max_word_length: int,
) -> None:
    scripts = sorted(ocr.available_scripts)  # Hans before Hant
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

        cap = capture_around(x, y)
        ix, iy = cap.to_image_coords(x, y)
        matches = []
        for script in scripts:
            text = text_at_point(
                ocr.recognize(cap.image, script), ix, iy, max_word_length
            )
            if text:
                matches = dictionary.match_prefixes(text)
                if matches:
                    break

        if matches:
            results.put(("show", matches, x, y))
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
    if not ocr.available_scripts:
        messagebox.showerror("Zhongwen Reader — setup needed", LANGUAGE_PACK_HELP)
        sys.exit(1)

    dictionary = Dictionary.load(data_file("cedict_ts.u8"))
    popup = Popup(root, font_size=config.font_size)

    stop = threading.Event()
    paused = threading.Event()
    results: queue.Queue = queue.Queue()

    threading.Thread(
        target=worker,
        args=(stop, paused, results, dictionary, ocr,
              config.trigger_vk, config.max_word_length),
        daemon=True,
    ).start()

    def on_quit():
        stop.set()
        root.after(0, root.destroy)

    start_tray(paused, on_quit)

    def poll_results():
        try:
            msg = None
            while True:
                msg = results.get_nowait()
        except queue.Empty:
            pass
        if msg:
            if msg[0] == "show":
                _, matches, x, y = msg
                popup.show(matches, x, y)
            else:
                popup.hide()
        root.after(30, poll_results)

    poll_results()
    root.mainloop()


if __name__ == "__main__":
    main()
