from zhongwen_reader.dictionary import Entry, Match
from zhongwen_reader.popup import TONE_COLORS
from zhongwen_reader.providers.chinese import build_segments


def test_tone_colors_defined_for_all_tones():
    assert set(TONE_COLORS) == {1, 2, 3, 4, 5}


def make_match():
    return Match(
        word="图书馆",
        entries=[
            Entry(
                traditional="圖書館",
                simplified="图书馆",
                pinyin="tu2 shu1 guan3",
                definitions=["library", "CL:家[jia1]"],
            )
        ],
    )


def test_build_segments_headword_shows_both_scripts_when_different():
    segments = build_segments([make_match()])
    kinds = [s[0] for s in segments]
    texts = [s[1] for s in segments]
    assert ("hanzi", "图书馆", None) == segments[0]
    assert ("hanzi_alt", "（圖書館）", None) in segments


def test_build_segments_single_script_when_same():
    match = Match(
        word="好",
        entries=[Entry("好", "好", "hao3", ["good"])],
    )
    segments = build_segments([match])
    assert not any(s[0] == "hanzi_alt" for s in segments)


def test_build_segments_pinyin_with_tones():
    segments = build_segments([make_match()])
    pinyin = [(s[1], s[2]) for s in segments if s[0] == "pinyin"]
    assert pinyin == [("tú", 2), ("shū", 1), ("guǎn", 3)]


def test_build_segments_definitions_joined():
    segments = build_segments([make_match()])
    defs = [s[1] for s in segments if s[0] == "definition"]
    assert defs == ["library; CL:家[jia1]"]
