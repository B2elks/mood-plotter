from pathlib import Path
from unittest.mock import patch

import pytest

from image_pipeline import generate_svg, png_to_svg


FIXTURE = Path(__file__).parent / "fixtures" / "test_image.png"


def test_png_to_svg_produces_svg_string():
    png_bytes = FIXTURE.read_bytes()
    svg = png_to_svg(png_bytes)
    assert svg.startswith("<?xml") or svg.startswith("<svg")
    assert "</svg>" in svg
    assert len(svg) > 100


def test_generate_svg_calls_dalle_then_vectorizes():
    fake_png = FIXTURE.read_bytes()

    with patch("image_pipeline._call_dalle", return_value=fake_png):
        svg = generate_svg(prompt="a happy moose", api_key="k")

    assert "<svg" in svg
    assert "</svg>" in svg


def test_generate_svg_raises_on_dalle_failure():
    with patch("image_pipeline._call_dalle", side_effect=RuntimeError("nope")):
        with pytest.raises(RuntimeError):
            generate_svg(prompt="x", api_key="k")
