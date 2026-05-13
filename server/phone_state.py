"""Mutable storage av telefonnumret som ska ringas — sparas till JSON-fil
sa det overlever restarts. Default fran env-variabeln USER_PHONE_NUMBER.
"""
import json
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)


def get_phone(state_path: Path, default: str) -> str:
    """Las nuvarande nummer fran state-filen, eller fallback till default."""
    try:
        if state_path.is_file():
            data = json.loads(state_path.read_text())
            phone = data.get("phone", "").strip()
            if phone:
                return phone
    except Exception as e:
        log.warning("phone_state: kunde inte lasa %s: %s", state_path, e)
    return default


def set_phone(state_path: Path, phone: str) -> str:
    """Skriv nytt nummer till state-filen. Returnerar normaliserade numret."""
    norm = normalize(phone)
    state_path.write_text(json.dumps({"phone": norm}, ensure_ascii=False))
    return norm


def normalize(phone: str) -> str:
    """Normalisera till +46-format. Tomma indata kastar ValueError."""
    s = re.sub(r"[\s\-()]", "", phone or "")
    if not s:
        raise ValueError("tom strang")
    if s.startswith("00"):
        s = "+" + s[2:]
    elif s.startswith("0"):
        s = "+46" + s[1:]
    elif not s.startswith("+"):
        s = "+" + s
    if not re.fullmatch(r"\+\d{8,15}", s):
        raise ValueError(f"ogiltigt nummer: {phone}")
    return s
