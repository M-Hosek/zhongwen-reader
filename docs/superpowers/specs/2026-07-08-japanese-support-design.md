# Japanese Support for Zhongwen Reader — Design

Date: 2026-07-08. Approved by user in brainstorming session.

## Goal

One app, both languages: hold the trigger key, hover over Chinese **or**
Japanese text anywhere on screen, get a popup with readings and English
definitions. Language is switched manually via the tray menu (中文 / 日本語)
and persisted in config. Fully offline, as today.

## User decisions

- Single exe with a manual language switch (no auto-detect: kanji-only words
  like 学生 are valid in both languages, so detection would guess wrong).
- Japanese readings shown as kana only (no romaji).
- Deinflection is rule-based (Rikaichan/Yomitan style), not a morphological
  analyzer — small, fast, testable, proven for hover dictionaries.

## Architecture: language providers

Refactor to a small provider interface so everything else stays shared:

```
src/zhongwen_reader/
├── providers/
│   ├── __init__.py      # Provider protocol + get_provider(name)
│   ├── chinese.py       # wraps existing dictionary.py + pinyin.py
│   └── japanese.py      # JMdict lookup + deinflection + kana readings
├── deinflect.py         # rule-based Japanese deinflection engine
├── jmdict.py            # JMdict parser (build-time) + compact loader (runtime)
```

**Provider protocol** (duck-typed):

- `name` — "chinese" | "japanese"
- `ocr_scripts` — OCR engine preference order (e.g. ["Hans", "Hant"] / ["Ja"])
- `is_word_char(ch)` — which characters the OCR cursor-mapping accepts
  (Chinese: Han ranges as today; Japanese: Han + hiragana 3040-309F +
  katakana 30A0-30FF + ー)
- `lookup(text)` — candidate string starting at the cursor → list of matches,
  best first, each already flattened to popup segments

**Popup** renders segments generically. Existing kinds stay; Japanese adds
`reading` (kana, single color) and `inflection` (e.g. "← 食べる (past polite)").
Chinese output is unchanged (tone-colored pinyin).

**OCR module** loses its hardcoded `is_cjk` filter in `text_at_point`; the
char predicate is passed in by the active provider. Japanese OCR engine tag:
`ja-JP` (script key "Ja").

**Tray** gains a language radio (中文 / 日本語) that swaps the active provider
at runtime and saves `language` to config. Startup uses the config value
(default "chinese"). Missing OCR pack for the selected language → same guided
dialog as today, mentioning 日本語 pack for Japanese.

## JMdict pipeline

- Source: JMdict_e (English glosses) from EDRDG, ~200k entries, XML.
- Build-time script `build_jmdict.py` converts XML → compact TSV-like file
  `data/jmdict_e.tsv` (kanji forms | kana readings | part-of-speech tags |
  glosses), analogous to cedict_ts.u8. Bundled by PyInstaller.
- Runtime loader indexes by every kanji form AND every kana reading
  (kana-only words like ひらがな must resolve).
- License: JMdict is CC BY-SA 4.0 (EDRDG). Credit in README like CC-CEDICT.

## Deinflection

`deinflect.py`: a table of rules `(suffix_from, suffix_to, from_pos, to_pos)`
applied breadth-first up to depth 4, tracking the chain of rule names for
display. Covers: polite forms (ます/ました/ません), past た/だ, negative
ない/なかった, て/で forms, potential, passive, causative, imperative,
conditional (たら/れば), volitional, たい, godan/ichidan stem changes, and
い-adjective conjugations (くない/かった/くて etc.). Each candidate is
validated against JMdict **with part-of-speech agreement** (a candidate ending
in る deinflected as ichidan must match an entry tagged v1) to suppress false
positives.

`lookup(text)`: for each prefix of the candidate string (longest first),
try direct JMdict hits, then deinflection candidates. Direct hits rank above
deinflected hits of the same length; longer matches rank above shorter.

## Naming

The app outgrew "Zhongwen": rename user-visible strings to handle both
languages gracefully but KEEP the package/repo/exe names unchanged (README
gets one line noting Japanese support). Renaming the project is out of scope.

## Error handling

- Japanese OCR pack missing → dialog with install instructions
  (Language.OCR~~~ja-JP~0.0.1.0), app stays usable for Chinese.
- Deinflection produces no valid entry → fall back to any direct
  shorter-prefix matches, else no popup (same as Chinese behavior).

## Testing

- Unit: JMdict line parsing, kana/kanji indexing, every deinflection rule
  (e.g. 食べました→食べる, 飲まなかった→飲む, 高かった→高い, 来て→来る),
  POS-agreement filtering, provider char predicates.
- Integration: rendered Japanese text through real Windows ja-JP OCR.
- End-to-end: pixel test with Japanese text + packaged exe smoke test.
- Regression: full existing Chinese test suite stays green.
