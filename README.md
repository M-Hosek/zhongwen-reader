# Zhongwen Reader

A system-wide Chinese popup dictionary for Windows, inspired by the
[Zhongwen](https://github.com/cschiller/zhongwen) browser extension — but for
anything on your screen: Word documents, PDFs in Acrobat (including scanned
pages), or any other window.

**Hold `Ctrl` and hover the mouse over Chinese text.** A popup appears next to
the cursor showing the word, tone-colored pinyin, and English definitions.
Release `Ctrl` and it disappears. Everything runs offline on your computer —
no cloud services, no tracking, no internet needed.

- Longest word first: hovering the 图 in 图书馆 shows 图书馆 (library), then
  图书, then 图 — just like Zhongwen.
- Both simplified and traditional characters are recognized and displayed.
- Pinyin tone colors: 1 = red, 2 = orange, 3 = green, 4 = blue, neutral = gray.

## Using the app

1. Double-click `ZhongwenReader.exe`. A red 中 icon appears in the system tray
   (bottom-right corner of the taskbar, possibly behind the `^` arrow).
2. Open any document with Chinese text.
3. Hold `Ctrl` and hover over a character. Move the mouse along the text and
   the popup follows.
4. Right-click the tray icon to **Pause** (temporarily disable) or **Quit**.

Tips:

- If a character is misread, zoom the document a little — bigger on-screen
  text means better recognition.
- To start the app automatically at login, press `Win+R`, type
  `shell:startup`, and put a shortcut to the exe in the folder that opens.

## Settings

Edit `%APPDATA%\ZhongwenReader\config.json` (created on first run), then
restart the app:

| Setting | Default | Meaning |
|---|---|---|
| `trigger_key` | `"ctrl"` | Key to hold: `"ctrl"`, `"alt"`, or `"shift"` |
| `font_size` | `12` | Popup text size |
| `max_word_length` | `8` | Longest dictionary word to match |

## Requirements

Windows 10/11 with a Chinese OCR language pack (a free Windows component; the
app tells you if it's missing). To add one: **Settings → Time & Language →
Language & region → Add a language** → 中文(中华人民共和国) for simplified or
中文(台湾) for traditional. This does not change your display language.

Or from an administrator terminal:

    dism /online /add-capability /capabilityname:Language.OCR~~~zh-CN~0.0.1.0
    dism /online /add-capability /capabilityname:Language.OCR~~~zh-TW~0.0.1.0

## Building from source

```powershell
python -m venv .venv
.venv\Scripts\pip install -e .[dev]
.venv\Scripts\python -m pytest                    # run tests
$env:PYTHONPATH="src"; .venv\Scripts\python -m zhongwen_reader   # run from source
.venv\Scripts\python build_icon.py               # generate icon
.venv\Scripts\pyinstaller build.spec --noconfirm # build dist\ZhongwenReader.exe
```

## How it works

Screenshot a strip around the cursor → Windows' built-in offline OCR →
map the cursor to a character → longest-match lookup in CC-CEDICT → popup.
See [docs/HOW_IT_WAS_MADE.md](docs/HOW_IT_WAS_MADE.md) for the full
architecture, design decisions, and testing approach.

## Known limitations

- Recognition accuracy depends on on-screen text size; zooming helps.
- Vertical text layout is not supported.
- Windows only (relies on Windows' OCR engine).

## Credits and licenses

- Dictionary data: [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cedict),
  © CC-CEDICT contributors, licensed
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
  (`data/cedict_ts.u8`, unmodified).
- Inspired by the [Zhongwen](https://github.com/cschiller/zhongwen) Chrome
  extension by Christian Schiller.
- Application code: MIT License (see `LICENSE`).
