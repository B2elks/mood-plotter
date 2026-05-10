from pathlib import Path
from unittest.mock import patch

import pytest

from tts_live import generate_ack_mp3


def test_generate_ack_mp3_writes_file_and_returns_url(tmp_path):
    fake_audio = b"fake-mp3-bytes"

    with patch("tts_live._call_elevenlabs", return_value=fake_audio):
        url = generate_ack_mp3(
            text="Förträffligt min herre",
            call_id="abc123",
            audio_dir=tmp_path,
            public_base_url="https://example.com",
            voice_id="voice-x",
            api_key="key",
        )

    assert url == "https://example.com/audio/ack_abc123.mp3"
    assert (tmp_path / "ack_abc123.mp3").read_bytes() == fake_audio


def test_generate_ack_mp3_returns_fallback_url_on_error(tmp_path):
    (tmp_path / "ack_fallback.mp3").write_bytes(b"fallback")

    with patch("tts_live._call_elevenlabs", side_effect=RuntimeError("boom")):
        url = generate_ack_mp3(
            text="x",
            call_id="abc",
            audio_dir=tmp_path,
            public_base_url="https://example.com",
            voice_id="v",
            api_key="k",
        )

    assert url == "https://example.com/audio/ack_fallback.mp3"
