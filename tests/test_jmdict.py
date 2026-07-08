import gzip
import textwrap

import pytest

from zhongwen_reader.jmdict import JMdict, JEntry, convert_xml, parse_tsv_line

SAMPLE_XML = textwrap.dedent(
    """\
    <?xml version="1.0" encoding="UTF-8"?>
    <JMdict>
    <entry>
    <ent_seq>1358280</ent_seq>
    <k_ele><keb>食べる</keb></k_ele>
    <k_ele><keb>喰べる</keb></k_ele>
    <r_ele><reb>たべる</reb></r_ele>
    <sense>
    <pos>&v1;</pos>
    <pos>&vt;</pos>
    <gloss>to eat</gloss>
    </sense>
    <sense>
    <gloss>to live on (e.g. a salary)</gloss>
    <gloss>to subsist on</gloss>
    </sense>
    </entry>
    <entry>
    <ent_seq>1169870</ent_seq>
    <r_ele><reb>ひらがな</reb></r_ele>
    <sense>
    <pos>&n;</pos>
    <gloss>hiragana</gloss>
    </sense>
    </entry>
    </JMdict>
    """
)


@pytest.fixture()
def tsv_path(tmp_path):
    xml_path = tmp_path / "JMdict_e"
    xml_path.write_text(SAMPLE_XML, encoding="utf-8")
    out = tmp_path / "jmdict_e.tsv.gz"
    convert_xml(xml_path, out)
    return out


def test_convert_produces_one_line_per_entry(tsv_path):
    with gzip.open(tsv_path, "rt", encoding="utf-8") as f:
        lines = [l for l in f.read().splitlines() if l]
    assert len(lines) == 2


def test_parse_tsv_line_roundtrip(tsv_path):
    with gzip.open(tsv_path, "rt", encoding="utf-8") as f:
        entry = parse_tsv_line(f.readline())
    assert entry.kanji == ["食べる", "喰べる"]
    assert entry.readings == ["たべる"]
    assert "v1" in entry.pos and "vt" in entry.pos
    assert entry.senses == ["to eat", "to live on (e.g. a salary); to subsist on"]


def test_kana_only_entry_has_no_kanji(tsv_path):
    dictionary = JMdict.load(tsv_path)
    entries = dictionary.lookup("ひらがな")
    assert len(entries) == 1
    assert entries[0].kanji == []
    assert entries[0].senses == ["hiragana"]


def test_lookup_by_kanji_and_by_reading(tsv_path):
    dictionary = JMdict.load(tsv_path)
    assert dictionary.lookup("食べる")[0].senses[0] == "to eat"
    assert dictionary.lookup("喰べる")[0].senses[0] == "to eat"
    assert dictionary.lookup("たべる")[0].senses[0] == "to eat"


def test_lookup_unknown_returns_empty(tsv_path):
    assert JMdict.load(tsv_path).lookup("砂糖") == []
