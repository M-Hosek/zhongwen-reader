"""Rule-based Japanese deinflection (Rikaichan-style).

`deinflect(surface)` returns candidate dictionary forms reachable by undoing
conjugations, each with a part-of-speech filter for JMdict validation and a
human-readable reason chain. Candidates are NOT guaranteed to be real words —
the caller must validate them against the dictionary (with POS agreement).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

MAX_DEPTH = 4


@dataclass(frozen=True)
class Candidate:
    word: str
    pos_filter: frozenset[str] | None  # None = no constraint (surface form)
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Rule:
    suffix: str
    replacement: str
    pos: frozenset[str] | None  # POS of the RESULTING dictionary form
    reason: str
    whole_word_ok: bool = False  # rule may consume the entire word (来る forms)


def _build_rules() -> list[Rule]:
    rules: list[Rule] = []

    def add(suffix, replacement, pos, reason, whole_word_ok=False):
        rules.append(
            Rule(
                suffix,
                replacement,
                frozenset(pos) if pos else None,
                reason,
                whole_word_ok,
            )
        )

    # --- Godan verbs: generated per consonant row ---------------------------
    # ending: (pos tags, i-stem, a-stem, e-stem, o-stem, ta-form, te-form)
    godan = {
        "う": (["v5u"], "い", "わ", "え", "お", "った", "って"),
        "く": (["v5k", "v5k-s"], "き", "か", "け", "こ", "いた", "いて"),
        "ぐ": (["v5g"], "ぎ", "が", "げ", "ご", "いだ", "いで"),
        "す": (["v5s"], "し", "さ", "せ", "そ", "した", "して"),
        "つ": (["v5t"], "ち", "た", "て", "と", "った", "って"),
        "ぬ": (["v5n"], "に", "な", "ね", "の", "んだ", "んで"),
        "ぶ": (["v5b"], "び", "ば", "べ", "ぼ", "んだ", "んで"),
        "む": (["v5m"], "み", "ま", "め", "も", "んだ", "んで"),
        "る": (["v5r", "v5r-i", "v5aru"], "り", "ら", "れ", "ろ", "った", "って"),
    }
    for u, (pos, i, a, e, o, ta, te) in godan.items():
        add(i + "ます", u, pos, "polite")
        add(i + "ました", u, pos, "polite past")
        add(i + "ません", u, pos, "polite negative")
        add(i + "たい", u, pos, "desiderative")
        add(a + "ない", u, pos, "negative")
        add(a + "なかった", u, pos, "past negative")
        add(a + "れる", u, pos, "passive")
        add(a + "せる", u, pos, "causative")
        add(a + "ず", u, pos, "without doing")
        add(ta, u, pos, "past")
        add(te, u, pos, "te-form")
        add(ta + "ら", u, pos, "conditional")
        add(e + "る", u, pos, "potential")
        add(e + "ば", u, pos, "provisional")
        add(e, u, pos, "imperative")
        add(o + "う", u, pos, "volitional")

    # 行く and compounds conjugate った/って despite ending in く
    for k, plain in (("行", "行く"), ("い", "いく")):
        add(k + "った", plain, ["v5k-s"], "past")
        add(k + "って", plain, ["v5k-s"], "te-form")

    # --- Ichidan verbs: stem = dictionary form minus る ----------------------
    v1 = ["v1", "v1-s"]
    for suffix, reason in [
        ("ます", "polite"),
        ("ました", "polite past"),
        ("ません", "polite negative"),
        ("ない", "negative"),
        ("なかった", "past negative"),
        ("た", "past"),
        ("て", "te-form"),
        ("たら", "conditional"),
        ("られる", "passive/potential"),
        ("させる", "causative"),
        ("ず", "without doing"),
        ("れば", "provisional"),
        ("ろ", "imperative"),
        ("よう", "volitional"),
        ("たい", "desiderative"),
    ]:
        add(suffix, "る", v1, reason)

    # --- Progressive/resultative: reduce to te-form, then chain -------------
    for prog in ["ている", "ていた", "ています", "ていました", "てる", "てた"]:
        add(prog, "て", None, "progressive")
    for prog in ["でいる", "でいた", "でいます", "でいました", "でる", "でた"]:
        add(prog, "で", None, "progressive")

    # --- い-adjectives -------------------------------------------------------
    adj = ["adj-i"]
    for suffix, reason in [
        ("かった", "past"),
        ("くない", "negative"),
        ("くなかった", "past negative"),
        ("くて", "te-form"),
        ("ければ", "provisional"),
        ("く", "adverbial"),
        ("さ", "noun form"),
    ]:
        add(suffix, "い", adj, reason)

    # --- する / noun+する ------------------------------------------------------
    vs = ["vs-i", "vs"]
    for suffix, reason in [
        ("します", "polite"),
        ("しました", "polite past"),
        ("しません", "polite negative"),
        ("した", "past"),
        ("して", "te-form"),
        ("しない", "negative"),
        ("しなかった", "past negative"),
        ("される", "passive"),
        ("させる", "causative"),
        ("すれば", "provisional"),
        ("しよう", "volitional"),
        ("したい", "desiderative"),
        ("しろ", "imperative"),
    ]:
        add(suffix, "する", vs, reason)
    add("する", "", ["vs"], "suru verb")

    # --- 来る ----------------------------------------------------------------
    vk = ["vk"]
    for kanji, kana in (("来", "来る"), ("き", "くる")):
        add(kanji + "ます", kana, vk, "polite", whole_word_ok=True)
        add(kanji + "ました", kana, vk, "polite past", whole_word_ok=True)
        add(kanji + "た", kana, vk, "past", whole_word_ok=True)
        add(kanji + "て", kana, vk, "te-form", whole_word_ok=True)
    add("来ない", "来る", vk, "negative", whole_word_ok=True)
    add("こない", "くる", vk, "negative", whole_word_ok=True)

    return rules


_RULES = _build_rules()


def deinflect(surface: str) -> list[Candidate]:
    """All candidate dictionary forms for `surface`, surface itself first."""
    results = [Candidate(surface, None, ())]
    seen = {surface}
    queue = deque([(surface, (), 0)])
    while queue:
        word, reasons, depth = queue.popleft()
        if depth >= MAX_DEPTH:
            continue
        for rule in _RULES:
            if not word.endswith(rule.suffix):
                continue
            stem = word[: -len(rule.suffix)]
            if not stem and not rule.whole_word_ok:
                continue
            new_word = stem + rule.replacement
            if new_word in seen:
                continue
            seen.add(new_word)
            new_reasons = reasons + (rule.reason,)
            results.append(Candidate(new_word, rule.pos, new_reasons))
            queue.append((new_word, new_reasons, depth + 1))
    return results
