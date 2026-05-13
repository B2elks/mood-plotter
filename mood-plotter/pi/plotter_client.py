"""WS-klient som tar emot SVG och kör AxiDraw."""
import json
import logging
import tempfile
import time
from pathlib import Path

import websocket
from pyaxidraw import axidraw

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("plotter-client")


def connect_axidraw():
    ad = axidraw.AxiDraw()
    ad.interactive()
    while not ad.connect():
        log.warning("AxiDraw inte ansluten — försöker igen om 5s")
        time.sleep(5)
    ad.options.pen_pos_down = config.AXIDRAW_PEN_POS_DOWN
    ad.options.pen_pos_up = config.AXIDRAW_PEN_POS_UP
    ad.options.speed_pendown = config.AXIDRAW_SPEED_PENDOWN
    return ad


def plot_svg(ad, svg_text: str):
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        f.write(svg_text.encode())
        svg_path = f.name
    try:
        ad.plot_setup(svg_path)
        ad.options.preview = False
        ad.plot_run()
        log.info("Plot klar")
    finally:
        Path(svg_path).unlink(missing_ok=True)


def run():
    ad = connect_axidraw()
    backoff = 1

    while True:
        try:
            ws = websocket.create_connection(
                config.SERVER_WS_URL,
                # ping/pong-keepalive sa anslutningen inte timeoutar tystt
                ping_interval=20, ping_timeout=10,
                # ingen lasningstimeout — vi vill blockera tills server skickar
                timeout=None,
            )
            log.info("WS ansluten")
            backoff = 1

            ws.send(json.dumps({
                "method": "register",
                "params": {"token": config.PI_TOKEN, "pi_id": config.PI_ID},
            }))

            while True:
                raw = ws.recv()
                if not raw:
                    break
                msg = json.loads(raw)
                if msg.get("method") == "plot":
                    log.info("SVG mottagen, %d tecken — plottar", len(msg.get("svg", "")))
                    try:
                        plot_svg(ad, msg["svg"])
                    except Exception as e:
                        log.exception("Plot-fel: %s", e)
                    ws.send(json.dumps({"method": "ready"}))
        except Exception as e:
            log.error("WS-fel: %s — reconnect om %ds", e, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    run()
