from zhongwen_reader.pinyin import accent_syllable, syllable_tone, format_pinyin


def test_accent_basic_tones():
    assert accent_syllable("zhong1") == "zhōng"
    assert accent_syllable("wen2") == "wén"
    assert accent_syllable("hao3") == "hǎo"
    assert accent_syllable("shi4") == "shì"


def test_accent_neutral_tone_drops_number():
    assert accent_syllable("ma5") == "ma"


def test_accent_umlaut():
    assert accent_syllable("lu:4") == "lǜ"
    assert accent_syllable("nu:3") == "nǚ"


def test_accent_placement_on_correct_vowel():
    # a/e take the mark; in "ou" the o does; else last vowel
    assert accent_syllable("hao3") == "hǎo"
    assert accent_syllable("lei2") == "léi"
    assert accent_syllable("dou4") == "dòu"
    assert accent_syllable("gui4") == "guì"


def test_accent_erhua_and_non_pinyin_passthrough():
    assert accent_syllable("r5") == "r"
    assert accent_syllable("·") == "·"


def test_syllable_tone():
    assert syllable_tone("zhong1") == 1
    assert syllable_tone("wen2") == 2
    assert syllable_tone("ma5") == 5
    assert syllable_tone("·") == 5


def test_format_pinyin_string():
    # Returns list of (accented_syllable, tone) pairs for coloring
    assert format_pinyin("Zhong1 guo2") == [("Zhōng", 1), ("guó", 2)]
