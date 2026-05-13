"""Mutable storage for PIR enable-flag — sparas till JSON-fil sa det
overlever restarts. Default: paslagen.
"""
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def get_enabled(state_path: Path, default: bool = True) -> bool:
    try:
        if state_path.is_file():
            data = json.loads(state_path.read_text())
            return bool(data.get("enabled", default))
    except Exception as e:
        log.warning("pir_state: kunde inte lasa %s: %s", state_path, e)
    return default


def set_enabled(state_path: Path, enabled: bool) -> bool:
    state_path.write_text(json.dumps({"enabled": bool(enabled)}))
    return bool(enabled)
