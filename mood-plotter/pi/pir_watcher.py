"""Läs PIR-sensor, skicka HTTP-trigger till servern med debounce."""
import logging
import time

import requests
from gpiozero import MotionSensor

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("pir-watcher")


def trigger_server():
    try:
        resp = requests.post(
            f"{config.SERVER_URL}/trigger",
            headers={"Authorization": f"Bearer {config.PI_TOKEN}"},
            json={"pi_id": config.PI_ID},
            timeout=5,
        )
        log.info("trigger → %d %s", resp.status_code, resp.text[:100])
    except Exception as e:
        log.error("Trigger-fel: %s", e)


def main():
    log.info("Startar PIR-watcher på GPIO %d", config.PIR_GPIO_PIN)
    pir = MotionSensor(config.PIR_GPIO_PIN)
    last_trigger = 0.0

    while True:
        pir.wait_for_motion()
        now = time.time()
        if now - last_trigger < config.PIR_DEBOUNCE_SECONDS:
            log.debug("Debounce-block, hoppar över")
            pir.wait_for_no_motion()
            continue
        last_trigger = now
        log.info("Rörelse detekterad → triggar")
        trigger_server()
        pir.wait_for_no_motion()


if __name__ == "__main__":
    main()
