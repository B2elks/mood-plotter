from elks_handler import (
    build_answer_response,
    build_record_action,
    build_record_response,
    build_hangup_response,
    verify_signature,
)


def test_build_answer_response_returns_play_with_next_url():
    resp = build_answer_response(
        play_url="https://example.com/q.mp3",
        after_play_url="https://example.com/after_play",
    )
    assert resp == {
        "play": "https://example.com/q.mp3",
        "next": "https://example.com/after_play",
    }


def test_build_record_action_returns_record_url():
    resp = build_record_action(record_callback="https://example.com/recording")
    assert resp == {"record": "https://example.com/recording"}


def test_build_record_response_returns_play_only():
    resp = build_record_response(play_url="https://example.com/ack.mp3")
    assert resp == {"play": "https://example.com/ack.mp3"}


def test_build_hangup_response_is_empty_dict():
    assert build_hangup_response() == {}


def test_verify_signature_accepts_valid_signature():
    api_password = "test-pass"
    url = "https://example.com/callback"
    import base64
    import hashlib
    import hmac

    sig = base64.b64encode(
        hmac.new(api_password.encode(), url.encode(), hashlib.sha256).digest()
    ).decode()

    assert verify_signature(api_password, url, sig) is True


def test_verify_signature_rejects_invalid_signature():
    assert verify_signature("test-pass", "https://example.com/cb", "wrongsig") is False


import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from elks_handler import initiate_call


@pytest.mark.asyncio
async def test_initiate_call_posts_to_46elks(mocker):
    mock_post = MagicMock()
    mock_post.return_value.__aenter__ = AsyncMock()
    mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_post.return_value.__aenter__.return_value.status = 200
    mock_post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value={"id": "call-123", "state": "ongoing"}
    )

    with patch("aiohttp.ClientSession.post", mock_post):
        result = await initiate_call(
            api_username="u",
            api_password="p",
            from_number="+46111",
            to_number="+46222",
            voice_start_url="https://x/answer",
            whenhangup_url="https://x/hangup",
        )

    assert result == "call-123"


@pytest.mark.asyncio
async def test_initiate_call_returns_none_on_error(mocker):
    mock_post = MagicMock()
    mock_post.return_value.__aenter__ = AsyncMock()
    mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_post.return_value.__aenter__.return_value.status = 400
    mock_post.return_value.__aenter__.return_value.text = AsyncMock(
        return_value="bad request"
    )

    with patch("aiohttp.ClientSession.post", mock_post):
        result = await initiate_call(
            api_username="u",
            api_password="p",
            from_number="+46111",
            to_number="+46222",
            voice_start_url="https://x/answer",
            whenhangup_url="https://x/hangup",
        )

    assert result is None
