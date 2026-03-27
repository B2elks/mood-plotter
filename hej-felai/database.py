import sqlite3
import os
import glob
from config import DATABASE, UPLOAD_DIR, DEFAULT_SETTINGS


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            link TEXT DEFAULT '',
            photo_filename TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
    conn.commit()
    conn.close()


def add_checkin(name, role, link, photo_filename):
    conn = get_db()
    conn.execute(
        "INSERT INTO checkins (name, role, link, photo_filename) VALUES (?, ?, ?, ?)",
        (name, role, link, photo_filename),
    )
    conn.commit()
    conn.close()


def get_checkins():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, role, link, photo_filename, created_at FROM checkins ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    result = dict(DEFAULT_SETTINGS)
    for r in rows:
        result[r["key"]] = r["value"]
    return result


def update_setting(key, value):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


def reset_all():
    conn = get_db()
    conn.execute("DELETE FROM checkins")
    conn.commit()
    conn.close()
    for f in glob.glob(os.path.join(UPLOAD_DIR, "*")):
        os.remove(f)
