import textwrap

import pytest

from zhongwen_reader.dictionary import Dictionary, Entry, parse_cedict_line

SAMPLE_CEDICT = textwrap.dedent(
    """\
    # CC-CEDICT sample
    #! version=1
    中國 中国 [Zhong1 guo2] /China/
    圖書館 图书馆 [tu2 shu1 guan3] /library/CL:家[jia1],個|个[ge4]/
    圖書 图书 [tu2 shu1] /books (in a library or bookstore)/CL:本[ben3]/
    圖 图 [tu2] /diagram/picture/drawing/chart/map/to plan/
    書 书 [shu1] /book/letter/document/CL:本[ben3],冊|册[ce4],部[bu4]/
    好 好 [hao3] /good/well/proper/
    好 好 [hao4] /to be fond of/to have a tendency to/
    """
)


@pytest.fixture()
def dictionary(tmp_path):
    path = tmp_path / "cedict_ts.u8"
    path.write_text(SAMPLE_CEDICT, encoding="utf-8")
    return Dictionary.load(path)


def test_parse_line_extracts_fields():
    entry = parse_cedict_line("中國 中国 [Zhong1 guo2] /China/")
    assert entry == Entry(
        traditional="中國",
        simplified="中国",
        pinyin="Zhong1 guo2",
        definitions=["China"],
    )


def test_parse_line_multiple_definitions():
    entry = parse_cedict_line("圖 图 [tu2] /diagram/picture/map/")
    assert entry.definitions == ["diagram", "picture", "map"]


def test_parse_line_skips_comments_and_blank():
    assert parse_cedict_line("# a comment") is None
    assert parse_cedict_line("") is None


def test_lookup_simplified_word(dictionary):
    entries = dictionary.lookup("图书馆")
    assert len(entries) == 1
    assert entries[0].definitions[0] == "library"


def test_lookup_traditional_word(dictionary):
    entries = dictionary.lookup("圖書館")
    assert len(entries) == 1
    assert entries[0].definitions[0] == "library"


def test_lookup_unknown_returns_empty(dictionary):
    assert dictionary.lookup("xyz") == []


def test_lookup_groups_multiple_entries_same_headword(dictionary):
    entries = dictionary.lookup("好")
    assert {e.pinyin for e in entries} == {"hao3", "hao4"}


def test_match_prefixes_returns_longest_first(dictionary):
    # Cursor over 图 in running text 图书馆里 -> 图书馆, 图书, 图
    matches = dictionary.match_prefixes("图书馆里")
    words = [m.word for m in matches]
    assert words == ["图书馆", "图书", "图"]
    assert matches[0].entries[0].definitions[0] == "library"


def test_match_prefixes_traditional_text(dictionary):
    matches = dictionary.match_prefixes("圖書館里")
    assert [m.word for m in matches] == ["圖書館", "圖書", "圖"]


def test_match_prefixes_no_match(dictionary):
    assert dictionary.match_prefixes("abc") == []
