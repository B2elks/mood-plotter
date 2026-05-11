import json
import time

from card_store import Card, list_cards, load_meta, save_card


def test_save_card_writes_files(tmp_path):
    card = save_card(
        cards_dir=tmp_path,
        call_id="abc123",
        png_bytes=b"PNGDATA",
        svg_text="<svg/>",
        transcription="trött",
        image_prompt="a peaceful forest",
        butler_ack="Förträffligt min herre",
    )

    assert card.call_id == "abc123"
    assert card.png_name.endswith("_abc123.png")
    assert card.svg_name.endswith("_abc123.svg")
    assert (tmp_path / card.png_name).read_bytes() == b"PNGDATA"
    assert (tmp_path / card.svg_name).read_text() == "<svg/>"

    meta_path = tmp_path / card.png_name.replace(".png", ".json")
    meta = json.loads(meta_path.read_text())
    assert meta["transcription"] == "trött"
    assert meta["image_prompt"] == "a peaceful forest"
    assert meta["butler_ack"] == "Förträffligt min herre"


def test_list_cards_returns_newest_first(tmp_path):
    save_card(tmp_path, "first", b"x", "<svg/>")
    time.sleep(1.05)
    save_card(tmp_path, "second", b"x", "<svg/>")

    cards = list_cards(tmp_path)
    assert len(cards) == 2
    assert cards[0].call_id == "second"
    assert cards[1].call_id == "first"


def test_list_cards_empty_dir_returns_empty_list(tmp_path):
    assert list_cards(tmp_path) == []


def test_list_cards_missing_dir_returns_empty(tmp_path):
    assert list_cards(tmp_path / "nope") == []


def test_load_meta_returns_full_metadata(tmp_path):
    save_card(
        tmp_path,
        "abc",
        b"x",
        "<svg/>",
        transcription="trött",
        image_prompt="forest",
        butler_ack="förträffligt",
    )

    meta = load_meta(tmp_path, "abc")
    assert meta is not None
    assert meta["transcription"] == "trött"
    assert meta["image_prompt"] == "forest"


def test_load_meta_missing_returns_none(tmp_path):
    assert load_meta(tmp_path, "nope") is None
