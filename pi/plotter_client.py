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


def plot_svg(svg_text: str):
    """En plot = en farsk AxiDraw-anslutning. Robust mot trasiga USB-state
    mellan korten (gamla varianten holl 'ad' for evigt och fick I/O-fel).

    plot_setup/plot_run-varianten oppnar och stanger USB-handeln internt.
    """
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        f.write(svg_text.encode())
        svg_path = f.name
    try:
        ad = axidraw.AxiDraw()
        ad.plot_setup(svg_path)
        ad.options.pen_pos_down = config.AXIDRAW_PEN_POS_DOWN
        ad.options.pen_pos_up = config.AXIDRAW_PEN_POS_UP
        ad.options.speed_pendown = config.AXIDRAW_SPEED_PENDOWN
        ad.options.preview = False
        ad.plot_run()
        log.info("Plot klar")
    finally:
        Path(svg_path).unlink(missing_ok=True)


def run():
    log.info("Plotter-klient startad, vantar pa SVG via WS")
    backoff = 1

    while True:
        try:
            ws = websocket.create_connection(
                config.SERVER_WS_URL,
                ping_interval=20, ping_timeout=10,
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
                        plot_svg(msg["svg"])
                    except Exception as e:
                        log.exception("Plot-fel: %s", e)
                    try:
                        ws.send(json.dumps({"method": "ready"}))
                    except Exception:
                        # broken pipe — vi reconnectar pa nasta iteration
                        break
        except Exception as e:
            log.error("WS-fel: %s — reconnect om %ds", e, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    run()
