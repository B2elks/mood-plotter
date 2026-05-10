"""Hantera WebSocket-anslutna AxiDraw-klienter."""
import logging

log = logging.getLogger(__name__)


class WSDispatcher:
    def __init__(self):
        self._clients: dict = {}

    def register(self, ws, pi_id: str):
        self._clients[ws] = {"pi_id": pi_id, "ready": True}
        log.info("Klient registrerad: %s (totalt: %d)", pi_id, len(self._clients))

    def unregister(self, ws):
        info = self._clients.pop(ws, None)
        if info:
            log.info("Klient bortkopplad: %s (kvar: %d)", info["pi_id"], len(self._clients))

    def mark_ready(self, ws):
        if ws in self._clients:
            self._clients[ws]["ready"] = True

    def mark_busy(self, ws):
        if ws in self._clients:
            self._clients[ws]["ready"] = False

    def get_ready_client(self):
        for ws, info in self._clients.items():
            if info["ready"]:
                return ws
        return None

    async def send_svg(self, svg: str) -> bool:
        """Skicka SVG till första ready-klienten. Returnerar True om någon fick den.

        Vid send-fel (t.ex. död WebSocket): unregistrera klienten och försök
        nästa ready. Förhindrar att en client fastnar i busy-state om sockeln
        dör mellan mark_busy och mark_ready.
        """
        while True:
            ws = self.get_ready_client()
            if ws is None:
                log.warning("Ingen ready-klient — SVG kastas")
                return False
            try:
                await ws.send_json({"method": "plot", "svg": svg})
                self.mark_busy(ws)
                return True
            except Exception as e:
                log.warning("Send-fel till klient — unregistrerar: %s", e)
                self.unregister(ws)
