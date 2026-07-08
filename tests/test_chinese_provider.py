import textwrap

import pytest

from zhongwen_reader.providers import get_provider

SAMPLE_CEDICT = textwrap.dedent(
    """\
    圖書館 图书馆 [tu2 shu1 guan3] /library/
    圖書 图书 [tu2 shu1] /books/
    圖 图 [tu2] /diagram/map/
    """
)


@pytest.fixture()
def provider(tmp_path):
    (tmp_path / "cedict_ts.u8").write_text(SAMPLE_CEDICT, encoding="utf-8")
    return get_provider("chinese", tmp_path)


def test_provider_identity(provider):
    assert provider.name == "chinese"
    assert provider.ocr_scripts == ["Hans", "Hant"]


def test_is_word_char(provider):
    assert provider.is_word_char("图")
    assert not provider.is_word_char("あ")  # kana is not Chinese
    assert not provider.is_word_char("a")


def test_lookup_returns_segments_longest_first(provider):
    segments = provider.lookup("图书馆里")
    hanzi = [s[1] for s in segments if s[0] == "hanzi"]
    assert hanzi == ["图书馆", "图书", "图"]
    assert ("hanzi_alt", "（圖書館）", None) in segments
    pinyin = [(s[1], s[2]) for s in segments if s[0] == "pinyin"]
    assert ("tú", 2) in pinyin


def test_lookup_no_match_returns_empty(provider):
    assert provider.lookup("abc") == []


def test_unknown_provider_name_raises(tmp_path):
    with pytest.raises(ValueError):
        get_provider("klingon", tmp_path)
