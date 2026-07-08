import gzip

import pytest

from zhongwen_reader.providers import get_provider

SAMPLE_TSV = "\n".join(
    [
        "食べる|喰べる\tたべる\tv1,vt\tto eat",
        "図書館\tとしょかん\tn\tlibrary",
        "図書\tとしょ\tn\tbooks",
        "ひらがな\tひらがな\tn\thiragana",
        "切る\tきる\tv5r,vt\tto cut",
        "着る\tきる\tv1,vt\tto wear",
        "勉強\tべんきょう\tn,vs\tstudy",
    ]
)


@pytest.fixture()
def provider(tmp_path):
    with gzip.open(tmp_path / "jmdict_e.tsv.gz", "wt", encoding="utf-8") as f:
        f.write(SAMPLE_TSV + "\n")
    return get_provider("japanese", tmp_path)


def kinds(segments, kind):
    return [s[1] for s in segments if s[0] == kind]


def test_provider_identity(provider):
    assert provider.name == "japanese"
    assert provider.ocr_scripts == ["Ja"]


def test_is_word_char_accepts_kana_and_kanji(provider):
    for ch in "図あアーば々":
        assert provider.is_word_char(ch), ch
    assert not provider.is_word_char("a")
    assert not provider.is_word_char("。")


def test_direct_lookup_longest_first(provider):
    segments = provider.lookup("図書館で")
    heads = kinds(segments, "hanzi")
    assert heads[0] == "図書館"
    assert "図書" in heads
    assert "としょかん" in kinds(segments, "reading")
    assert any("library" in d for d in kinds(segments, "definition"))


def test_deinflected_lookup_shows_dictionary_form_and_reason(provider):
    segments = provider.lookup("食べました")
    assert "食べる" in kinds(segments, "hanzi")
    assert "たべる" in kinds(segments, "reading")
    inflections = kinds(segments, "inflection")
    assert any("polite past" in i for i in inflections)


def test_pos_agreement_disambiguates(provider):
    # 切って is the te-form of godan 切る; ichidan 着る must NOT match
    segments = provider.lookup("切って")
    defs = " ".join(kinds(segments, "definition"))
    assert "to cut" in defs
    assert "to wear" not in defs
    # 着て is the te-form of ichidan 着る
    segments = provider.lookup("着て")
    defs = " ".join(kinds(segments, "definition"))
    assert "to wear" in defs


def test_kana_only_word(provider):
    segments = provider.lookup("ひらがなを")
    assert "ひらがな" in kinds(segments, "hanzi")


def test_suru_verb(provider):
    segments = provider.lookup("勉強した")
    assert "勉強" in kinds(segments, "hanzi")
    assert any("study" in d for d in kinds(segments, "definition"))


def test_no_match_returns_empty(provider):
    assert provider.lookup("abc") == []
