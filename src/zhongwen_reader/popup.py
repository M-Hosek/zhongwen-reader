"""Frameless always-on-top popup rendering provider segments near the cursor."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

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

CURSOR_OFFSET = (16, 22)

# (kind, text, tone) — kinds: hanzi, hanzi_alt, pinyin, reading, inflection,
# definition, separator. Providers produce these; the popup only renders.
Segment = tuple[str, str, int | None]


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
        self._base_font = base_font
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
        self._text.tag_configure(
            "reading",
            font=tkfont.Font(family="Segoe UI", size=font_size, weight="bold"),
            foreground="#7fd4c3",
        )
        self._text.tag_configure(
            "inflection",
            font=tkfont.Font(family="Segoe UI", size=font_size - 1, slant="italic"),
            foreground=FG_ALT,
        )

        # Map once invisibly so the Text widget gets its real wrap width;
        # an unmapped widget is 1px wide and line/pixel counts are garbage.
        self._win.attributes("-alpha", 0.0)
        self._win.deiconify()
        self._win.update()
        self._win.withdraw()
        self._win.attributes("-alpha", 1.0)

    def show(self, segments: list[Segment], screen_x: int, screen_y: int) -> None:
        if not segments:
            self.hide()
            return
        self._render(segments)
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
                # Start a new line unless at the top or right after a
                # separator, which already ends with a newline.
                if text.index("end-1c") != "1.0" and text.get("end-2c") != "\n":
                    text.insert("end", "\n")
                text.insert("end", content, "hanzi")
            elif kind == "hanzi_alt":
                text.insert("end", content, "hanzi_alt")
            elif kind == "pinyin":
                text.insert("end", "  " if tone is None else " ")
                text.insert("end", content, f"tone{tone}")
            elif kind == "reading":
                text.insert("end", "  ")
                text.insert("end", content, "reading")
            elif kind == "inflection":
                text.insert("end", "  ")
                text.insert("end", content, "inflection")
            elif kind == "definition":
                text.insert("end", "\n" + content, "definition")
        # Size the widget by rendered pixel height: `height` is measured in
        # base-font lines, but hanzi lines use a larger font, so counting
        # display lines undershoots and clips the bottom.
        text.update_idletasks()
        pixels = text.count("1.0", "end", "update", "ypixels")
        lines = -(-pixels // self._base_font.metrics("linespace"))
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
