import pytest

from tts_cache import pick_question_url


def test_pick_question_url_returns_url_to_existing_file(tmp_path):
    audio_dir = tmp_path
    (audio_dir / "q_01.mp3").write_bytes(b"x")
    (audio_dir / "q_02.mp3").write_bytes(b"x")

    url = pick_question_url(
        audio_dir=audio_dir,
        public_base_url="https://example.com",
    )

    assert url in (
        "https://example.com/audio/q_01.mp3",
        "https://example.com/audio/q_02.mp3",
    )


def test_pick_question_url_raises_if_no_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        pick_question_url(
            audio_dir=tmp_path,
            public_base_url="https://example.com",
        )


def test_pick_question_url_only_picks_q_prefix_files(tmp_path):
    audio_dir = tmp_path
    (audio_dir / "q_01.mp3").write_bytes(b"x")
    (audio_dir / "ack_xyz.mp3").write_bytes(b"x")
    (audio_dir / "junk.txt").write_text("x")

    for _ in range(20):
        url = pick_question_url(
            audio_dir=audio_dir,
            public_base_url="https://example.com",
        )
        assert url.endswith("q_01.mp3")
