"""Spara genererade kort (PNG + SVG + meta-JSON) på disk för galleriet."""
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class Card:
    call_id: str
    timestamp: float
    png_name: str
    svg_name: str

    @property
    def iso_time(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.timestamp))


def save_card(
    cards_dir: Path,
    call_id: str,
    png_bytes: bytes,
    svg_text: str,
    transcription: str = "",
    image_prompt: str = "",
    butler_ack: str = "",
) -> Card:
    """Spara PNG + SVG + meta. Returnera Card-objekt."""
    cards_dir = Path(cards_dir)
    cards_dir.mkdir(parents=True, exist_ok=True)

    now = time.time()
    stem = f"{time.strftime('%Y%m%d_%H%M%S', time.localtime(now))}_{call_id}"
    png_name = f"{stem}.png"
    svg_name = f"{stem}.svg"
    meta_name = f"{stem}.json"

    (cards_dir / png_name).write_bytes(png_bytes)
    (cards_dir / svg_name).write_text(svg_text)
    (cards_dir / meta_name).write_text(json.dumps({
        "call_id": call_id,
        "timestamp": now,
        "png": png_name,
        "svg": svg_name,
        "transcription": transcription,
        "image_prompt": image_prompt,
        "butler_ack": butler_ack,
    }, ensure_ascii=False, indent=2))

    log.info("Sparade kort %s (%d B PNG, %d B SVG)", stem, len(png_bytes), len(svg_text))
    return Card(call_id=call_id, timestamp=now, png_name=png_name, svg_name=svg_name)


def list_cards(cards_dir: Path) -> list[Card]:
    """Lista alla kort, nyaste först."""
    cards_dir = Path(cards_dir)
    if not cards_dir.is_dir():
        return []

    cards: list[Card] = []
    for meta_path in cards_dir.glob("*.json"):
        try:
            data = json.loads(meta_path.read_text())
            cards.append(Card(
                call_id=data["call_id"],
                timestamp=float(data["timestamp"]),
                png_name=data["png"],
                svg_name=data["svg"],
            ))
        except Exception as e:
            log.warning("Kunde inte läsa %s: %s", meta_path, e)

    cards.sort(key=lambda c: c.timestamp, reverse=True)
    return cards


def load_meta(cards_dir: Path, call_id: str) -> dict | None:
    """Hämta full meta för ett kort (för admin-vyn)."""
    cards_dir = Path(cards_dir)
    for meta_path in cards_dir.glob(f"*_{call_id}.json"):
        try:
            return json.loads(meta_path.read_text())
        except Exception as e:
            log.warning("Kunde inte läsa %s: %s", meta_path, e)
            return None
    return None
