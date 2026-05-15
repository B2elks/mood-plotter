"""Mutable storage for interaction mode: 'voice' (default) eller 'sms'."""
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

VALID = ("voice", "sms")


def get_mode(state_path: Path, default: str = "voice") -> str:
    try:
        if state_path.is_file():
            data = json.loads(state_path.read_text())
            mode = data.get("mode")
            if mode in VALID:
                return mode
    except Exception as e:
        log.warning("mode_state: kunde inte lasa %s: %s", state_path, e)
    return default


def set_mode(state_path: Path, mode: str) -> str:
    if mode not in VALID:
        raise ValueError(f"ogiltigt mode: {mode}; tillaten: {VALID}")
    state_path.write_text(json.dumps({"mode": mode}))
    return mode
