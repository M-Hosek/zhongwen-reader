from zhongwen_reader.deinflect import deinflect


def forms(word):
    """All candidate dictionary forms for a surface word."""
    return {c.word for c in deinflect(word)}


def pos_filter_for(word, target):
    return next(c.pos_filter for c in deinflect(word) if c.word == target)


def test_identity_candidate_always_included():
    assert "図書館" in forms("図書館")
    assert next(c for c in deinflect("図書館") if c.word == "図書館").pos_filter is None


def test_ichidan_conjugations():
    assert "食べる" in forms("食べます")
    assert "食べる" in forms("食べました")
    assert "食べる" in forms("食べません")
    assert "食べる" in forms("食べない")
    assert "食べる" in forms("食べなかった")
    assert "食べる" in forms("食べた")
    assert "食べる" in forms("食べて")
    assert "食べる" in forms("食べられる")
    assert "食べる" in forms("食べれば")
    assert "食べる" in forms("食べよう")
    assert "食べる" in forms("食べたい")


def test_godan_rows():
    assert "飲む" in forms("飲まなかった")
    assert "飲む" in forms("飲みました")
    assert "書く" in forms("書いた")
    assert "泳ぐ" in forms("泳いで")
    assert "話す" in forms("話しました")
    assert "待つ" in forms("待って")
    assert "死ぬ" in forms("死んだ")
    assert "遊ぶ" in forms("遊んで")
    assert "読む" in forms("読んだ")
    assert "帰る" in forms("帰った")
    assert "買う" in forms("買いました")
    assert "書く" in forms("書ける")  # potential
    assert "行く" in forms("行けば")  # conditional
    assert "飲む" in forms("飲もう")  # volitional


def test_progressive_chains_through_te_form():
    assert "食べる" in forms("食べている")
    assert "書く" in forms("書いている")
    assert "読む" in forms("読んでいる")


def test_passive_past_chains():
    assert "買う" in forms("買われた")
    assert "食べる" in forms("食べられた")


def test_desiderative_negative_chains():
    # 食べたくない -> 食べたい -> 食べる
    assert "食べる" in forms("食べたくない")


def test_i_adjective_conjugations():
    assert "高い" in forms("高かった")
    assert "高い" in forms("高くない")
    assert "高い" in forms("高くなかった")
    assert "高い" in forms("高くて")
    assert "高い" in forms("高ければ")


def test_suru_verb_strips_to_noun():
    assert "勉強" in forms("勉強した")
    assert "勉強" in forms("勉強します")
    assert pos_filter_for("勉強した", "勉強") == frozenset({"vs"})


def test_kuru():
    assert "来る" in forms("来た")
    assert "来る" in forms("来て")
    assert "来る" in forms("来ない")
    assert "くる" in forms("きました")


def test_pos_filters_constrain_lookup():
    # 食べた deinflected to 食べる must be validated as an ichidan verb
    f = pos_filter_for("食べた", "食べる")
    assert f is not None and "v1" in f


def test_no_spurious_deinflection_of_plain_nouns():
    # 学生 should only yield itself
    assert forms("学生") == {"学生"}


def test_reasons_chain_is_reported():
    cand = next(c for c in deinflect("食べました") if c.word == "食べる")
    assert "polite past" in " ".join(cand.reasons)
