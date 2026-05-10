"""mood-plotter aiohttp-server."""
import asyncio
import logging
import uuid
from pathlib import Path

from aiohttp import web

import config
import elks_handler
import image_pipeline
import tts_cache
import tts_live
import voice_butler
from cooldown import Cooldown
from ws_dispatcher import WSDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("mood-plotter")


def _check_auth(request) -> bool:
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {config.PI_TOKEN}"


async def trigger_handler(request):
    if not _check_auth(request):
        return web.Response(status=401, text="unauthorized")

    cd: Cooldown = request.app["cooldown"]
    if not cd.try_acquire():
        return web.Response(status=429, text="cooldown")

    dispatcher: WSDispatcher = request.app["ws_dispatcher"]
    if not config.DRY_RUN and dispatcher.get_ready_client() is None:
        cd.release()
        return web.Response(status=503, text="no plotter ready")

    call_id = str(uuid.uuid4())[:8]
    request.app["pending_calls"][call_id] = {"state": "calling"}

    if config.DRY_RUN:
        log.info(
            "[DRY_RUN] skulle ringa %s, call_id=%s",
            config.USER_PHONE_NUMBER,
            call_id,
        )
        return web.json_response({"call_id": call_id, "dry_run": True})

    elks_id = await elks_handler.initiate_call(
        api_username=config.ELKS_API_USERNAME,
        api_password=config.ELKS_API_PASSWORD,
        from_number=config.ELKS_FROM_NUMBER,
        to_number=config.USER_PHONE_NUMBER,
        voice_start_url=f"{config.SERVER_PUBLIC_URL}/elks/answer?call_id={call_id}",
        whenhangup_url=f"{config.SERVER_PUBLIC_URL}/elks/hangup?call_id={call_id}",
    )
    if elks_id is None:
        cd.release()
        request.app["pending_calls"].pop(call_id, None)
        return web.Response(status=502, text="elks call failed")

    request.app["pending_calls"][call_id]["elks_id"] = elks_id
    return web.json_response({"call_id": call_id, "elks_id": elks_id})


async def elks_answer_handler(request):
    call_id = request.query.get("call_id", "")
    # Update state so a hangup-after-answer doesn't release the cooldown.
    if call_id in request.app["pending_calls"]:
        request.app["pending_calls"][call_id]["state"] = "answered"
    play_url = tts_cache.pick_question_url(
        audio_dir=config.AUDIO_DIR,
        public_base_url=config.SERVER_PUBLIC_URL,
    )
    record_callback = (
        f"{config.SERVER_PUBLIC_URL}/elks/recording?call_id={call_id}"
    )
    log.info("call_id=%s answer -> fraga %s", call_id, play_url)
    return web.json_response(
        elks_handler.build_answer_response(play_url, record_callback)
    )


async def elks_recording_handler(request):
    call_id = request.query.get("call_id", "")
    data = await request.post()
    recording_url = data.get("recordurl") or data.get("url", "")
    log.info("call_id=%s inspelning klar: %s", call_id, recording_url)

    # Synchronously: download recording, transcribe, analyze, generate ack MP3.
    # This blocks the 46elks recording-callback for ~3-6s, but it tolerates that
    # and it's the only way to return the personalized ack URL.
    ack_url = f"{config.SERVER_PUBLIC_URL}/audio/ack_fallback.mp3"
    image_prompt = None
    try:
        import aiohttp as _aiohttp

        wav_path = config.AUDIO_DIR / f"rec_{call_id}.wav"
        async with _aiohttp.ClientSession() as session:
            async with session.get(recording_url) as resp:
                wav_path.write_bytes(await resp.read())

        text = voice_butler.transcribe_audio(wav_path, config.OPENAI_API_KEY)
        log.info("call_id=%s transkribering: %r", call_id, text)

        result = voice_butler.analyze_response(text, config.OPENAI_API_KEY)
        log.info(
            "call_id=%s prompt: %s | ack: %s",
            call_id,
            result.image_prompt[:60],
            result.butler_ack[:60],
        )
        image_prompt = result.image_prompt

        ack_url = tts_live.generate_ack_mp3(
            text=result.butler_ack,
            call_id=call_id,
            audio_dir=config.AUDIO_DIR,
            public_base_url=config.SERVER_PUBLIC_URL,
            voice_id=config.ELEVENLABS_VOICE_ID,
            api_key=config.ELEVENLABS_API_KEY,
        )

        wav_path.unlink(missing_ok=True)
    except Exception as e:
        log.exception("call_id=%s fel i synchronous pipeline: %s", call_id, e)

    # Background: image generation + plotter dispatch (slow, fire-and-forget).
    if image_prompt:
        asyncio.create_task(_generate_and_plot(request.app, call_id, image_prompt))

    return web.json_response(elks_handler.build_record_response(ack_url))


async def _generate_and_plot(app, call_id: str, image_prompt: str):
    """Bakgrundstask: DALL.E -> vpype -> skicka SVG till plotter."""
    try:
        svg = image_pipeline.generate_svg(image_prompt, config.OPENAI_API_KEY)
        sent = await app["ws_dispatcher"].send_svg(svg)
        log.info("call_id=%s SVG skickad till plotter: %s", call_id, sent)
    except Exception as e:
        log.exception("call_id=%s fel i _generate_and_plot: %s", call_id, e)


async def elks_hangup_handler(request):
    call_id = request.query.get("call_id", "")
    pending = request.app["pending_calls"].pop(call_id, None)
    if pending and pending.get("state") == "calling":
        request.app["cooldown"].release()
        log.info("call_id=%s missat samtal - cooldown rensad", call_id)
    return web.json_response({})


async def audio_handler(request):
    name = request.match_info["name"]
    if "/" in name or ".." in name:
        return web.Response(status=400)
    path = config.AUDIO_DIR / name
    if not path.is_file():
        return web.Response(status=404)
    return web.FileResponse(path)


async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    dispatcher: WSDispatcher = request.app["ws_dispatcher"]
    pi_id = "unknown"
    registered = False

    async for msg in ws:
        if msg.type != web.WSMsgType.TEXT:
            continue
        try:
            data = msg.json()
        except Exception:
            continue

        method = data.get("method")
        if method == "register":
            params = data.get("params", {})
            if params.get("token") != config.PI_TOKEN:
                await ws.close(code=4401, message=b"unauthorized")
                return ws
            pi_id = params.get("pi_id", "unknown")
            dispatcher.register(ws, pi_id=pi_id)
            registered = True
            await ws.send_json({"method": "registered"})
        elif method == "ready":
            dispatcher.mark_ready(ws)

    if registered:
        dispatcher.unregister(ws)
    return ws


def create_app():
    app = web.Application()
    app["cooldown"] = Cooldown(config.COOLDOWN_DB, config.COOLDOWN_SECONDS)
    app["ws_dispatcher"] = WSDispatcher()
    app["pending_calls"] = {}

    app.router.add_post("/trigger", trigger_handler)
    app.router.add_get("/elks/answer", elks_answer_handler)
    app.router.add_post("/elks/answer", elks_answer_handler)
    app.router.add_post("/elks/recording", elks_recording_handler)
    app.router.add_get("/elks/hangup", elks_hangup_handler)
    app.router.add_post("/elks/hangup", elks_hangup_handler)
    app.router.add_get("/audio/{name}", audio_handler)
    app.router.add_get("/ws", ws_handler)

    return app


def main():
    app = create_app()
    web.run_app(app, host="127.0.0.1", port=config.PORT)


if __name__ == "__main__":
    main()
