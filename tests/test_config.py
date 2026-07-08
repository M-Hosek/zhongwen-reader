import json

from zhongwen_reader.config import Config, load_config


def test_defaults_when_no_file(tmp_path):
    cfg = load_config(tmp_path / "missing.json")
    assert cfg == Config()
    assert cfg.trigger_key == "ctrl"
    assert cfg.font_size == 12
    assert cfg.max_word_length == 8


def test_file_overrides_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"trigger_key": "alt", "font_size": 16}))
    cfg = load_config(path)
    assert cfg.trigger_key == "alt"
    assert cfg.font_size == 16
    assert cfg.max_word_length == 8  # untouched default


def test_unknown_keys_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"bogus": 1, "font_size": 14}))
    cfg = load_config(path)
    assert cfg.font_size == 14


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not json")
    assert load_config(path) == Config()


def test_trigger_vk_codes():
    assert Config(trigger_key="ctrl").trigger_vk == 0x11
    assert Config(trigger_key="alt").trigger_vk == 0x12
    assert Config(trigger_key="shift").trigger_vk == 0x10
    assert Config(trigger_key="unknown").trigger_vk == 0x11  # safe fallback
