"""mood-plotter aiohttp-server."""
import asyncio
import base64
import json
import logging
import uuid
from pathlib import Path

from aiohttp import web

import audio_clips
import card_store
import config
import elks_handler
import image_pipeline
import templates
import tts_cache
import voice_butler
import ws_voice
from cooldown import Cooldown
from ws_dispatcher import WSDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("mood-plotter")


def _check_pi_auth(request) -> bool:
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {config.PI_TOKEN}"


def _check_admin_auth(request) -> bool:
    """HTTP Basic Auth: user='admin', password=ADMIN_PASSWORD."""
    if not config.ADMIN_PASSWORD:
        return False
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth[6:]).decode()
        user, _, pw = decoded.partition(":")
    except Exception:
        return False
    return user == "admin" and pw == config.ADMIN_PASSWORD


def _admin_unauthorized() -> web.Response:
    return web.Response(
        status=401,
        text="auth required",
        headers={"WWW-Authenticate": 'Basic realm="moodplotter admin"'},
    )


async def _start_call(app, dry_run: bool = False) -> tuple[int, dict]:
    """Gemensam logik for både /trigger och /admin/trigger.

    Returnerar (status, body)."""
    cd: Cooldown = app["cooldown"]
    if not cd.try_acquire():
        return 429, {"error": "cooldown"}

    dispatcher: WSDispatcher = app["ws_dispatcher"]
    # Med en plotter inkopplad kraver vi en ready klient. I server-utan-plotter
    # läget skippar vi check:en — då plottas bara på galleri-sidan.
    if (
        not config.DRY_RUN
        and not dry_run
        and not config.ALLOW_NO_PLOTTER
        and dispatcher.get_ready_client() is None
    ):
        cd.release()
        return 503, {"error": "no plotter ready"}

    call_id = str(uuid.uuid4())[:8]
    app["pending_calls"][call_id] = {"state": "calling"}

    if config.DRY_RUN or dry_run:
        log.info("[DRY_RUN] skulle ringa %s, call_id=%s", config.USER_PHONE_NUMBER, call_id)
        return 200, {"call_id": call_id, "dry_run": True}

    # Anvand WS-Voice-routing om WS_CONNECT_NUMBER ar satt (realtidsljud),
    # annars HTTP-record-vagen som fallback.
    if config.WS_CONNECT_NUMBER:
        voice_start = json.dumps({"connect": config.WS_CONNECT_NUMBER})
    else:
        voice_start = f"{config.SERVER_PUBLIC_URL}/elks/answer?call_id={call_id}"

    elks_id = await elks_handler.initiate_call(
        api_username=config.ELKS_API_USERNAME,
        api_password=config.ELKS_API_PASSWORD,
        from_number=config.ELKS_FROM_NUMBER,
        to_number=config.USER_PHONE_NUMBER,
        voice_start_url=voice_start,
        whenhangup_url=f"{config.SERVER_PUBLIC_URL}/elks/hangup?call_id={call_id}",
    )
    if elks_id is None:
        cd.release()
        app["pending_calls"].pop(call_id, None)
        return 502, {"error": "elks call failed"}

    app["pending_calls"][call_id]["elks_id"] = elks_id
    return 200, {"call_id": call_id, "elks_id": elks_id}


async def trigger_handler(request):
    if not _check_pi_auth(request):
        return web.Response(status=401, text="unauthorized")
    status, body = await _start_call(request.app)
    return web.json_response(body, status=status)


async def elks_answer_handler(request):
    call_id = request.query.get("call_id", "")
    if call_id in request.app["pending_calls"]:
        request.app["pending_calls"][call_id]["state"] = "answered"
    play_url = tts_cache.pick_question_url(
        audio_dir=config.AUDIO_DIR,
        public_base_url=config.SERVER_PUBLIC_URL,
    )
    after_play_url = f"{config.SERVER_PUBLIC_URL}/elks/after_play?call_id={call_id}"
    log.info("call_id=%s answer -> fraga %s", call_id, play_url)
    return web.json_response(
        elks_handler.build_answer_response(play_url, after_play_url)
    )


async def elks_after_play_handler(request):
    """Efter att fragan spelats, be 46elks spela in svaret."""
    call_id = request.query.get("call_id", "")
    record_callback = f"{config.SERVER_PUBLIC_URL}/elks/recording?call_id={call_id}"
    play_ack_url = f"{config.SERVER_PUBLIC_URL}/elks/play_ack?call_id={call_id}"
    log.info(
        "call_id=%s after_play -> record till %s, next %s",
        call_id, record_callback, play_ack_url,
    )
    return web.json_response(
        elks_handler.build_record_action(record_callback, play_ack_url)
    )


async def elks_recording_handler(request):
    """Tar emot inspelningen och kickar igang ALLT i bakgrund. Inget sync."""
    call_id = request.query.get("call_id", "")
    data = await request.post()
    recording_url = data.get("wav", "")
    duration = data.get("duration", "0")
    log.info(
        "call_id=%s inspelning klar (duration=%s): %s",
        call_id, duration, recording_url,
    )

    # Inget vantande — kor allt i bakgrund. play_ack spelar ack_neutral direkt.
    if recording_url:
        asyncio.create_task(
            _process_recording_background(request.app, call_id, recording_url)
        )
    return web.Response(text="")


async def _process_recording_background(app, call_id: str, recording_url: str):
    """Bakgrund: ladda ner wav, Whisper, LLM, DALL-E, vpype, spara kort."""
    try:
        import aiohttp as _aiohttp

        wav_path = config.AUDIO_DIR / f"rec_{call_id}.wav"
        auth = _aiohttp.BasicAuth(
            config.ELKS_API_USERNAME, config.ELKS_API_PASSWORD,
        )
        async with _aiohttp.ClientSession(auth=auth) as session:
            async with session.get(recording_url) as resp:
                wav_path.write_bytes(await resp.read())

        text = voice_butler.transcribe_audio(wav_path, config.OPENAI_API_KEY)
        log.info("call_id=%s transkribering: %r", call_id, text)

        result = voice_butler.analyze_response(text, config.OPENAI_API_KEY)
        log.info("call_id=%s image_prompt: %s", call_id, result.image_prompt[:80])

        png = image_pipeline.generate_png(result.image_prompt, config.OPENAI_API_KEY)
        svg = image_pipeline.png_to_svg(png)
        card_store.save_card(
            cards_dir=config.CARDS_DIR,
            call_id=call_id,
            png_bytes=png,
            svg_text=svg,
            transcription=text,
            image_prompt=result.image_prompt,
            butler_ack=result.butler_ack,
        )
        sent = await app["ws_dispatcher"].send_svg(svg)
        log.info("call_id=%s kort sparat + skickat till plotter: %s", call_id, sent)

        wav_path.unlink(missing_ok=True)
    except Exception as e:
        log.exception("call_id=%s fel i background-pipeline: %s", call_id, e)


async def elks_play_ack_handler(request):
    """46elks anropar denna direkt efter recording. Ingen vantan — slumpa
    en pre-recorded ack och spela direkt. 'next' chainas till /elks/end
    sa samtalet avslutas direkt nar ack-frasen ar klar."""
    call_id = request.query.get("call_id", "")
    ack_url = _pick_random_ack()
    end_url = f"{config.SERVER_PUBLIC_URL}/elks/end?call_id={call_id}"
    log.info("call_id=%s play_ack -> %s (instant)", call_id, ack_url)
    return web.json_response(elks_handler.build_record_response(ack_url, end_url))


async def elks_end_handler(request):
    """Avsluta samtalet direkt nar ack-frasen spelats klart."""
    call_id = request.query.get("call_id", "")
    log.info("call_id=%s end -> hangup", call_id)
    return web.json_response(elks_handler.build_end_response())


def _pick_random_ack() -> str:
    """Slumpa en ack-MP3 ur audio/. Foretrader ack_neutral_NN.mp3 sa nya
    varianter plockas upp automatiskt nar de droppas in."""
    import random
    candidates = sorted(config.AUDIO_DIR.glob("ack_neutral_*.mp3"))
    if not candidates:
        candidates = [config.AUDIO_DIR / "ack_neutral.mp3"]
    chosen = random.choice(candidates)
    return f"{config.SERVER_PUBLIC_URL}/audio/{chosen.name}"


async def elks_hangup_handler(request):
    call_id = request.query.get("call_id", "")
    pending = request.app["pending_calls"].pop(call_id, None)
    if pending and pending.get("state") == "calling":
        request.app["cooldown"].release()
        log.info("call_id=%s missat samtal - cooldown rensad", call_id)
    return web.json_response({})


async def audio_handler(request):
    return _serve_static(config.AUDIO_DIR, request.match_info["name"])


async def cards_handler(request):
    return _serve_static(config.CARDS_DIR, request.match_info["name"])


def _serve_static(base_dir: Path, name: str) -> web.Response:
    if "/" in name or ".." in name:
        return web.Response(status=400)
    path = base_dir / name
    if not path.is_file():
        return web.Response(status=404)
    return web.FileResponse(path)


async def gallery_handler(request):
    cards = card_store.list_cards(config.CARDS_DIR)
    html_str = templates.gallery_page(cards, config.SERVER_PUBLIC_URL)
    return web.Response(text=html_str, content_type="text/html")


async def admin_handler(request):
    if not _check_admin_auth(request):
        return _admin_unauthorized()
    cards = card_store.list_cards(config.CARDS_DIR)
    recent_metas = []
    for c in cards[:25]:
        meta = card_store.load_meta(config.CARDS_DIR, c.call_id)
        if meta:
            recent_metas.append(meta)
    html_str = templates.admin_page(cards, config.CARDS_DIR, recent_metas)
    return web.Response(text=html_str, content_type="text/html")


async def admin_trigger_handler(request):
    if not _check_admin_auth(request):
        return _admin_unauthorized()
    status, body = await _start_call(request.app)
    ok = status == 200
    msg = body.get("error") or f"Samtal startat (call_id={body.get('call_id','?')})"
    html_str = templates.admin_trigger_result(ok, msg)
    return web.Response(text=html_str, content_type="text/html", status=status)


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

    config.CARDS_DIR.mkdir(parents=True, exist_ok=True)
    config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # Forhandsladda PCM-klipp for WS Voice (snabb stromning under samtal).
    app["question_clips"] = audio_clips.load_clips(config.AUDIO_DIR, "q")
    app["ack_clips"] = audio_clips.load_clips(config.AUDIO_DIR, "ack_neutral")
    log.info(
        "Laddade %d fragor + %d ack-klipp till minnet",
        len(app["question_clips"]), len(app["ack_clips"]),
    )

    app.router.add_get("/", gallery_handler)
    app.router.add_get("/admin", admin_handler)
    app.router.add_post("/admin/trigger", admin_trigger_handler)
    app.router.add_get("/cards/{name}", cards_handler)
    app.router.add_post("/trigger", trigger_handler)
    app.router.add_get("/elks/answer", elks_answer_handler)
    app.router.add_post("/elks/answer", elks_answer_handler)
    app.router.add_get("/elks/after_play", elks_after_play_handler)
    app.router.add_post("/elks/after_play", elks_after_play_handler)
    app.router.add_get("/elks/play_ack", elks_play_ack_handler)
    app.router.add_post("/elks/play_ack", elks_play_ack_handler)
    app.router.add_get("/elks/end", elks_end_handler)
    app.router.add_post("/elks/end", elks_end_handler)
    app.router.add_post("/elks/recording", elks_recording_handler)
    app.router.add_get("/elks/hangup", elks_hangup_handler)
    app.router.add_post("/elks/hangup", elks_hangup_handler)
    app.router.add_get("/audio/{name}", audio_handler)
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/ws-voice", ws_voice.handle_ws_voice)

    return app


def main():
    app = create_app()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run_two_listeners(app))


async def _run_two_listeners(app):
    """Bind HTTP-rutter till 127.0.0.1 (via nginx) och /ws-voice till
    0.0.0.0:WS_VOICE_PORT (direktanslutning fran 46elks).

    Da exponerar vi inte /admin etc. utanfor nginx, men 46elks kan
    fortfarande na /ws-voice direkt utan TLS-terminering.
    """
    runner = web.AppRunner(app)
    await runner.setup()
    sites = [
        web.TCPSite(runner, "127.0.0.1", config.PORT),
        web.TCPSite(runner, "0.0.0.0", config.WS_VOICE_PORT),
    ]
    for site in sites:
        await site.start()
    log.info(
        "Lyssnar pa 127.0.0.1:%d (HTTP) och 0.0.0.0:%d (WS Voice)",
        config.PORT, config.WS_VOICE_PORT,
    )
    # Halva forever
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    main()
