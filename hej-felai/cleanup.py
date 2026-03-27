#!/usr/bin/env python3
"""Nightly cleanup — run via cron at 00:05 daily."""

import datetime
from database import reset_all

if __name__ == "__main__":
    reset_all()
    print(f"[{datetime.datetime.now().isoformat()}] Cleanup complete — all checkins and photos removed.")
