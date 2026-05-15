"""46elks webhook-actions och signaturkontroll."""
import base64
import hashlib
import hmac


def build_answer_response(play_url: str, after_play_url: str) -> dict:
    """Svar pa voice_start: spela fragan. 'next' ar URL-strang till nasta action.

    46elks kraver att 'next' ar en URL som returnerar nasta JSON-action,
    INTE ett nastlat action-objekt.
    """
    return {
        "play": play_url,
        "next": after_play_url,
    }


def build_record_action(record_callback: str, next_url: str) -> dict:
    """Svar efter att fragan spelats: be 46elks spela in svaret.

    silencedetection=yes (default) -- avsluta sa fort anvandaren tystnar,
        sa ack-frasen spelas direkt utan att vi vantar i onodan
    timelimit=10                   -- max-tak om nan pratar pa
    """
    return {
        "record": record_callback,
        "next": next_url,
        "silencedetection": "yes",
        "timelimit": 10,
    }


def build_record_response(play_url: str, end_url: str) -> dict:
    """Svar pa play_ack-callback: spela ack-fras, sen lagg pa via end_url.

    46elks haller samtalet oppet om man inte explicit chainar hangup.
    """
    return {
        "play": play_url,
        "next": end_url,
    }


def build_end_response() -> dict:
    """Avsluta samtalet."""
    return {"hangup": ""}


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


async def send_sms(
    api_username: str,
    api_password: str,
    from_number: str,
    to_number: str,
    message: str,
    sms_url: str | None = None,
) -> str | None:
    """Skicka SMS via 46elks. Om sms_url anges fangas svar dar.
    Returnerar SMS-id eller None."""
    payload = {
        "from": from_number,
        "to": to_number,
        "message": message,
    }
    if sms_url:
        payload["sms_url"] = sms_url
    auth = aiohttp.BasicAuth(api_username, api_password)
    try:
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(
                "https://api.46elks.com/a1/sms", data=payload
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("id")
                body = await resp.text()
                log.error("46elks SMS-fel %s: %s", resp.status, body)
                return None
    except Exception as e:
        log.exception("Fel vid SMS-utskick: %s", e)
        return None


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
