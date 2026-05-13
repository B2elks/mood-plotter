import pytest

from phone_state import get_phone, normalize, set_phone


def test_get_returns_default_when_file_missing(tmp_path):
    assert get_phone(tmp_path / "no.json", "+46111") == "+46111"


def test_set_and_get_roundtrip(tmp_path):
    p = tmp_path / "phone.json"
    set_phone(p, "+46760075573")
    assert get_phone(p, "+46999") == "+46760075573"


def test_normalize_swedish_local_to_plus46():
    assert normalize("0760075573") == "+46760075573"


def test_normalize_double_zero_to_plus():
    assert normalize("004631234567") == "+4631234567"


def test_normalize_strips_spaces_and_dashes():
    assert normalize("+46 760 075 573") == "+46760075573"
    assert normalize("+46-760-07-55-73") == "+46760075573"


def test_normalize_rejects_empty():
    with pytest.raises(ValueError):
        normalize("")


def test_normalize_rejects_letters():
    with pytest.raises(ValueError):
        normalize("hello")


def test_set_normalizes():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        from pathlib import Path
        p = Path(d) / "phone.json"
        result = set_phone(p, "0760075573")
        assert result == "+46760075573"
        assert get_phone(p, "x") == "+46760075573"
