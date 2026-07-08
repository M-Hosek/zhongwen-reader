# How Zhongwen Reader Was Made

This document explains the design decisions and architecture behind the app,
for anyone curious how it works or wanting to modify it.

## The problem

Browser popup dictionaries like the Zhongwen extension only work on web pages.
Reading Chinese in Word documents or PDFs (especially scanned ones) means
constant dictionary lookups by hand. The goal: hover the mouse over any Chinese
text on screen — in any program — and get an instant popup with pinyin and
definitions, fully offline.

## The key design decision: read pixels, not documents

There were three candidate approaches:

1. **Accessibility APIs** (UI Automation) — ask Word/Acrobat for the text under
   the cursor, the way screen readers do. Accurate in Word, but Acrobat's
   support is unreliable, and scanned PDFs have no text layer at all.
2. **Document parsing** — open the .docx/.pdf directly. Requires per-format
   code, can't tell what's under the *cursor*, and still fails on scans.
3. **Screen OCR** — screenshot the area around the cursor and recognize the
   characters from pixels.

Screen OCR won because one code path covers everything: Word, Acrobat,
scanned pages, browsers, chat apps. Windows 10/11 ships an offline OCR engine
(`Windows.Media.Ocr`) with good Chinese support, so no cloud service and no
bundled ML model is needed. The trade-off — accuracy depends on on-screen text
size — is acceptable because the popup shows what was recognized, making
errors visible, and zooming the document fixes them.

## Pipeline

Every ~30 ms while the trigger key (default `Ctrl`) is held:

1. **Trigger check** (`hotkey.py`) — `GetAsyncKeyState` via ctypes. No global
   keyboard hook needed, just polling a key's state.
2. **Capture** (`capture.py`) — `mss` grabs a 360×90 px strip centered on the
   cursor, upscaled 2× with Lanczos so the OCR engine sees larger glyphs.
3. **OCR** (`ocr.py`) — the strip goes through `Windows.Media.Ocr` (via the
   `winrt` Python bindings): PIL image → BMP bytes → `BitmapDecoder` →
   `SoftwareBitmap` → `recognize_async`. Simplified is tried first, then
   traditional; whichever yields dictionary hits wins.
4. **Cursor-to-character mapping** (`ocr.py`) — OCR returns per-word bounding
   boxes. Each word box is split evenly into per-character spans; the character
   whose span contains the cursor is the lookup start. The candidate string is
   that character plus the CJK characters following it on the same line.
5. **Dictionary lookup** (`dictionary.py`) — CC-CEDICT (~120k entries) is
   parsed at startup into a dict keyed by both simplified and traditional
   headwords. Longest-prefix matching finds every dictionary word starting at
   the cursor character, longest first — so 图书馆 shows as one word, then
   图书, then 图. Lookups take microseconds.
6. **Popup** (`popup.py`) — a frameless, always-on-top tkinter `Toplevel` with
   a `Text` widget. Pinyin syllables are colored by tone (Zhongwen-style:
   1=red, 2=orange, 3=green, 4=blue, neutral=gray) using text tags. Placement
   flips near screen edges.

## Threading model

tkinter must run on the main thread, so:

- **Main thread**: tk root + popup, draining a `queue.Queue` of show/hide
  messages every 30 ms via `root.after`.
- **Worker thread**: the hover loop (key check → capture → OCR → lookup),
  posting results to the queue. Debounced: skips work unless the cursor moved
  more than 4 px.
- **Tray thread**: `pystray` icon with Pause/Quit.

## The bug worth knowing about: DPI scaling

On displays scaled above 100%, a non-DPI-aware process sees *virtualized*
coordinates (e.g. 1280×800 on a 1920×1200 screen at 150%), while `mss`
captures *physical* pixels. Cursor position and screenshot coordinates
silently disagree, and the OCR finds nothing under the "cursor." The fix is
one call at startup — `SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2)` —
after which cursor, tkinter, and capture all speak physical pixels. This was
caught by an end-to-end test that rendered Chinese text in a real window and
ran the full pipeline against live screen pixels.

## Testing

Built test-first throughout:

- **Pure logic** (CC-CEDICT parsing, longest-match lookup, numbered-pinyin →
  accented conversion, cursor-to-character mapping, config): plain pytest
  units, written before the implementation.
- **OCR integration**: render known Chinese strings to images with Pillow and
  run the real Windows OCR engine on them (skipped automatically if the
  language pack is missing).
- **End-to-end**: scripts that display Chinese text in a real window, move the
  cursor there, synthesize a Ctrl keypress, and verify the popup actually
  renders on screen — run against both the source tree and the packaged exe.

## Packaging

PyInstaller builds a single windowed exe (`build.spec`), bundling the
CC-CEDICT data file. At startup the app checks which OCR language packs are
installed (`OcrEngine.try_create_from_language`) and shows install
instructions if none are found. The OCR packs are the one thing that can't be
bundled — they're Windows components, installed once via Settings or DISM:

    dism /online /add-capability /capabilityname:Language.OCR~~~zh-TW~0.0.1.0

## Stack summary

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.13 | Fast to build and modify |
| OCR | Windows.Media.Ocr via `winrt` | Offline, preinstalled, good Chinese support |
| Capture | `mss` | Fast raw screen grabs |
| Key state | ctypes `GetAsyncKeyState` | No hook, no dependency, no admin |
| UI | tkinter | Stdlib, sufficient for a popup |
| Tray | `pystray` | Simple, works with tkinter |
| Dictionary | CC-CEDICT | Free (CC BY-SA 4.0), both scripts, same data Zhongwen uses |
| Packaging | PyInstaller onefile | Double-clickable, no Python needed |
