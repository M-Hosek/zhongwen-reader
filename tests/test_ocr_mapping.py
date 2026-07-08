from zhongwen_reader.ocr import WordBox, text_at_point, is_cjk


def make_line(words_with_x, y=10, h=20, char_w=20):
    """Build WordBoxes on one line; words_with_x = [(text, x0), ...]."""
    return [
        WordBox(text=t, x=x, y=y, w=char_w * len(t), h=h)
        for t, x in words_with_x
    ]


def test_is_cjk():
    assert is_cjk("图")
    assert is_cjk("圖")
    assert not is_cjk("a")
    assert not is_cjk("1")
    assert not is_cjk("。")  # punctuation is not a word char


def test_cursor_on_first_char_returns_full_tail():
    lines = [make_line([("图书馆里", 100)])]
    # cursor over first char (100..120)
    assert text_at_point(lines, 110, 20) == "图书馆里"


def test_cursor_mid_word_starts_at_that_char():
    lines = [make_line([("图书馆里", 100)])]
    # third char occupies 140..160
    assert text_at_point(lines, 150, 20) == "馆里"


def test_cursor_spanning_multiple_wordboxes_concatenates():
    lines = [make_line([("图书", 100), ("馆里", 145)])]
    assert text_at_point(lines, 110, 20) == "图书馆里"


def test_cursor_outside_any_line_returns_empty():
    lines = [make_line([("图书馆", 100)])]
    assert text_at_point(lines, 110, 300) == ""
    assert text_at_point(lines, 500, 20) == ""


def test_cursor_over_non_cjk_returns_empty():
    lines = [make_line([("hello", 100), ("图书馆", 250)])]
    assert text_at_point(lines, 110, 20) == ""


def test_tail_stops_at_non_cjk():
    lines = [make_line([("图书馆abc", 100)])]
    assert text_at_point(lines, 110, 20) == "图书馆"


def test_max_chars_limit():
    lines = [make_line([("一二三四五六七八九十", 100)])]
    assert text_at_point(lines, 110, 20, max_chars=4) == "一二三四"
