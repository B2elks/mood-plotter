from elks_handler import (
    build_answer_response,
    build_record_response,
    build_hangup_response,
    verify_signature,
)


def test_build_answer_response_returns_play_with_next_record():
    resp = build_answer_response(
        play_url="https://example.com/q.mp3",
        record_callback="https://example.com/recording",
    )
    assert resp == {
        "play": "https://example.com/q.mp3",
        "next": {
            "record": {
                "timeout": 4,
                "maxlength": 8,
                "callbackurl": "https://example.com/recording",
            }
        },
    }


def test_build_record_response_returns_play_then_hangup():
    resp = build_record_response(play_url="https://example.com/ack.mp3")
    assert resp == {
        "play": "https://example.com/ack.mp3",
        "next": {"hangup": ""},
    }


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
