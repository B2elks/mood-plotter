import sqlite3
from datetime import datetime, timedelta
from config import DATABASE, KNOWN_NUMBER_DAYS


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS verifications (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL,
            phone TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            callback_url TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            verified_at DATETIME
        );
        CREATE INDEX IF NOT EXISTS idx_verifications_code ON verifications(code);
        CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status);

        CREATE TABLE IF NOT EXISTS known_numbers (
            phone TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            verified_at DATETIME NOT NULL,
            expires_at DATETIME NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def create_verification(vid, code, phone, name, callback_url):
    conn = get_db()
    conn.execute(
        "INSERT INTO verifications (id, code, phone, name, callback_url) VALUES (?, ?, ?, ?, ?)",
        (vid, code, phone, name, callback_url),
    )
    conn.commit()
    conn.close()


def get_verification(vid):
    conn = get_db()
    row = conn.execute("SELECT * FROM verifications WHERE id = ?", (vid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def find_pending_by_code(code):
    conn = get_db()
    cutoff = (datetime.utcnow() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    row = conn.execute(
        "SELECT * FROM verifications WHERE code = ? AND status = 'pending' AND created_at > ? ORDER BY created_at DESC LIMIT 1",
        (code.upper(), cutoff),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def mark_verified(vid, phone=None):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    if phone:
        conn.execute(
            "UPDATE verifications SET status = 'verified', verified_at = ?, phone = ? WHERE id = ?",
            (now, phone, vid),
        )
    else:
        conn.execute(
            "UPDATE verifications SET status = 'verified', verified_at = ? WHERE id = ?",
            (now, vid),
        )
    conn.commit()
    conn.close()
    return now


def upsert_known_number(phone, name):
    now = datetime.utcnow()
    expires = now + timedelta(days=KNOWN_NUMBER_DAYS)
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO known_numbers (phone, name, verified_at, expires_at) VALUES (?, ?, ?, ?)",
        (phone, name, now.strftime("%Y-%m-%d %H:%M:%S"), expires.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def lookup_number(phone):
    conn = get_db()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    row = conn.execute(
        "SELECT * FROM known_numbers WHERE phone = ? AND expires_at > ?",
        (phone, now),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM verifications").fetchone()[0]
    verified = conn.execute(
        "SELECT COUNT(*) FROM verifications WHERE status = 'verified'"
    ).fetchone()[0]
    cached = conn.execute("SELECT COUNT(*) FROM known_numbers").fetchone()[0]
    conn.close()
    return {"total": total, "verified": verified, "cached": cached}
