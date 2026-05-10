"""Cooldown-spärr i sqlite för att begränsa antal samtal per tidsfönster."""
import sqlite3
import time
from pathlib import Path


class Cooldown:
    def __init__(self, db_path: Path, seconds: int):
        self.db_path = Path(db_path)
        self.seconds = seconds
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._conn() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cooldown (id INTEGER PRIMARY KEY, "
                "last_acquired REAL NOT NULL)"
            )

    def try_acquire(self) -> bool:
        """Returnera True om vi får ringa, False om vi är inom cooldown."""
        now = time.time()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT last_acquired FROM cooldown WHERE id = 1"
            ).fetchone()
            if row and now - row[0] < self.seconds:
                return False
            conn.execute(
                "INSERT OR REPLACE INTO cooldown (id, last_acquired) VALUES (1, ?)",
                (now,),
            )
            return True

    def release(self):
        """Rensa cooldown så nästa try_acquire lyckas (vid t.ex. missat samtal)."""
        with self._conn() as conn:
            conn.execute("DELETE FROM cooldown WHERE id = 1")
