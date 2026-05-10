"""46elks webhook-actions och signaturkontroll."""
import base64
import hashlib
import hmac


def build_answer_response(play_url: str, record_callback: str) -> dict:
    """Svar på voice_start: spela frågan, spela in svaret."""
    return {
        "play": play_url,
        "next": {
            "record": {
                "timeout": 4,
                "maxlength": 8,
                "callbackurl": record_callback,
            }
        },
    }


def build_record_response(play_url: str) -> dict:
    """Svar på recording-callback: spela ack, lägg på."""
    return {
        "play": play_url,
        "next": {"hangup": ""},
    }


def build_hangup_response() -> dict:
    """Svar på whenhangup — ingen action behövs."""
    return {}


def verify_signature(api_password: str, callback_url: str, signature: str) -> bool:
    """Kontrollera 46elks X-46elks-Signature mot förväntad HMAC."""
    expected = base64.b64encode(
        hmac.new(
            api_password.encode(), callback_url.encode(), hashlib.sha256
        ).digest()
    ).decode()
    return hmac.compare_digest(expected, signature)
