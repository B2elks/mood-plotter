"""Easter eggs — predefinierade SVG som triggas av specifika SMS.

Lagg en .svg-fil i mappen `server/easter_eggs/` dar filnamnet (utan
extension) ar det SMS-ord som ska trigga den. Filnamn-konvention:
lowercase a-z, 0-9, eller underscore.

Matchningen ar exakt mot HELA SMS-texten efter normalisering (lowercase,
non-alfanumeriskt → underscore, kollapsade). Det betyder att slumpvisa
SMS inte triggar — bara nar texten EXAKT motsvarar ett egg-filnamn.

Easter-egg-plottar visas INTE i kiosk-galleriet (sparas inte i
card_store) och konsumerar inte DALL-E-credits.
"""
from pathlib import Path


EASTER_EGGS_DIR = Path(__file__).parent / "easter_eggs"


def normalize(text: str) -> str:
    """SMS-text → 'safe' nyckel med bara lowercase alnum + underscore.

    Exempel:
      'Marfar!'   → 'marfar'
      'Glada Pi' → 'glada_pi'
      '  HEJ  '  → 'hej'
    """
    text = text.strip().lower()
    out = []
    prev_us = False
    for ch in text:
        if ch.isalnum():
            out.append(ch)
            prev_us = False
        elif not prev_us:
            out.append("_")
            prev_us = True
    return "".join(out).strip("_")


def match_keyword(text: str) -> str | None:
    """Returnerar SVG-text om SMS-text matchar en egg-fil, annars None."""
    if not text:
        return None
    key = normalize(text)
    if not key:
        return None
    path = EASTER_EGGS_DIR / f"{key}.svg"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def list_keywords() -> list[str]:
    """Lista alla registrerade egg-nycklar (basenames utan .svg)."""
    if not EASTER_EGGS_DIR.is_dir():
        return []
    return sorted(p.stem for p in EASTER_EGGS_DIR.glob("*.svg"))
