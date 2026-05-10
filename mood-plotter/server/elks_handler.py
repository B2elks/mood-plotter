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


import json
import logging

import aiohttp

log = logging.getLogger(__name__)


async def initiate_call(
    api_username: str,
    api_password: str,
    from_number: str,
    to_number: str,
    voice_start_url: str,
    whenhangup_url: str,
) -> str | None:
    """Initiera utgående samtal. Returnerar elks call_id eller None."""
    payload = {
        "from": from_number,
        "to": to_number,
        "voice_start": voice_start_url,
        "whenhangup": whenhangup_url,
    }
    auth = aiohttp.BasicAuth(api_username, api_password)
    try:
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(
                "https://api.46elks.com/a1/calls", data=payload
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("id")
                body = await resp.text()
                log.error("46elks API-fel %s: %s", resp.status, body)
                return None
    except Exception as e:
        log.exception("Fel vid utgående samtal: %s", e)
        return None
