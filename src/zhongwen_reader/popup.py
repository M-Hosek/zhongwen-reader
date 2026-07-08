"""Frameless always-on-top popup showing dictionary matches near the cursor."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from .dictionary import Match
from .pinyin import format_pinyin

# Zhongwen-style tone colors: 1=red 2=orange 3=green 4=blue 5=neutral gray
TONE_COLORS = {
    1: "#ff4d4d",
    2: "#ffaa33",
    3: "#66d966",
    4: "#66a3ff",
    5: "#bbbbbb",
}

BG = "#1e1f24"
FG_HANZI = "#ffffff"
FG_ALT = "#9aa0ab"
FG_DEF = "#d8dbe0"

MAX_MATCHES = 4
CURSOR_OFFSET = (16, 22)

# Segment kinds: hanzi, hanzi_alt, pinyin, definition, separator
Segment = tuple[str, str, int | None]


def build_segments(matches: list[Match]) -> list[Segment]:
    """Flatten dictionary matches into (kind, text, tone) render segments."""
    segments: list[Segment] = []
    for i, match in enumerate(matches[:MAX_MATCHES]):
        if i:
            segments.append(("separator", "", None))
        for entry in match.entries:
            shown = match.word
            alt = entry.traditional if shown == entry.simplified else entry.simplified
            segments.append(("hanzi", shown, None))
            if alt != shown:
                segments.append(("hanzi_alt", f"（{alt}）", None))
            for syllable, tone in format_pinyin(entry.pinyin):
                segments.append(("pinyin", syllable, tone))
            segments.append(("definition", "; ".join(entry.definitions), None))
    return segments


class Popup:
    def __init__(self, root: tk.Tk, font_size: int = 12):
        self._root = root
        self._win = tk.Toplevel(root)
        self._win.withdraw()
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._text = tk.Text(
            self._win,
            bg=BG,
            bd=0,
            padx=10,
            pady=8,
            wrap="word",
            width=46,
            height=4,
            cursor="arrow",
            highlightthickness=1,
            highlightbackground="#3a3d46",
        )
        self._text.pack(fill="both", expand=True)

        hanzi_font = tkfont.Font(family="Microsoft YaHei", size=font_size + 6)
        base_font = tkfont.Font(family="Segoe UI", size=font_size)
        self._text.configure(font=base_font)
        self._text.tag_configure("hanzi", font=hanzi_font, foreground=FG_HANZI)
        self._text.tag_configure(
            "hanzi_alt",
            font=tkfont.Font(family="Microsoft YaHei", size=font_size + 2),
            foreground=FG_ALT,
        )
        for tone, color in TONE_COLORS.items():
            self._text.tag_configure(
                f"tone{tone}",
                font=tkfont.Font(family="Segoe UI", size=font_size, weight="bold"),
                foreground=color,
            )
        self._text.tag_configure("definition", foreground=FG_DEF)
        self._text.tag_configure("separator", foreground="#3a3d46")

    def show(self, matches: list[Match], screen_x: int, screen_y: int) -> None:
        if not matches:
            self.hide()
            return
        self._render(build_segments(matches))
        self._place(screen_x, screen_y)
        self._win.deiconify()

    def hide(self) -> None:
        self._win.withdraw()

    def _render(self, segments: list[Segment]) -> None:
        text = self._text
        text.configure(state="normal")
        text.delete("1.0", "end")
        for kind, content, tone in segments:
            if kind == "separator":
                text.insert("end", "\n" + "─" * 44 + "\n", "separator")
            elif kind == "hanzi":
                if text.index("end-1c") != "1.0":
                    text.insert("end", "\n")
                text.insert("end", content, "hanzi")
            elif kind == "hanzi_alt":
                text.insert("end", content, "hanzi_alt")
            elif kind == "pinyin":
                text.insert("end", "  " if tone is None else " ")
                text.insert("end", content, f"tone{tone}")
            elif kind == "definition":
                text.insert("end", "\n" + content, "definition")
        # Shrink the widget to its actual rendered line count.
        text.update_idletasks()
        lines = text.count("1.0", "end", "displaylines")[0]
        text.configure(height=min(lines, 24), state="disabled")

    def _place(self, screen_x: int, screen_y: int) -> None:
        win = self._win
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x = screen_x + CURSOR_OFFSET[0]
        y = screen_y + CURSOR_OFFSET[1]
        if x + w > sw:
            x = screen_x - w - CURSOR_OFFSET[0]
        if y + h > sh:
            y = screen_y - h - CURSOR_OFFSET[1]
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
