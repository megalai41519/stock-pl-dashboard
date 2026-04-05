"""
app/data/cache.py — SQLite-backed key/value cache with TTL.

• Auto-creates cache.db next to the executable on first run.
• TTL default: 15 minutes (CACHE_TTL_SEC from config).
• Thread-safe via a module-level lock.
"""

import sqlite3
import json
import time
import threading
import logging
from typing import Optional, Any

from app.config import CACHE_DB, CACHE_TTL_SEC

log = logging.getLogger(__name__)
_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_cache() -> None:
    """Create the cache table if it does not exist."""
    with _lock:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key       TEXT PRIMARY KEY,
                value     TEXT NOT NULL,
                cached_at REAL NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
    log.info("Cache initialised at %s", CACHE_DB)


def get(key: str) -> Optional[Any]:
    """Return cached value if present and not expired, else None."""
    with _lock:
        conn = _connect()
        row = conn.execute(
            "SELECT value, cached_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        conn.close()

    if row is None:
        return None

    age = time.time() - row["cached_at"]
    if age > CACHE_TTL_SEC:
        log.debug("Cache EXPIRED  key=%s  age=%.0fs", key, age)
        return None

    log.debug("Cache HIT      key=%s  age=%.0fs", key, age)
    return json.loads(row["value"])


def set(key: str, value: Any) -> None:
    """Persist a JSON-serialisable value."""
    payload = json.dumps(value)
    with _lock:
        conn = _connect()
        conn.execute(
            """
            INSERT INTO cache (key, value, cached_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                                           cached_at=excluded.cached_at
            """,
            (key, payload, time.time()),
        )
        conn.commit()
        conn.close()
    log.debug("Cache SET      key=%s", key)


def purge_expired() -> int:
    """Delete all expired entries. Returns number of rows removed."""
    cutoff = time.time() - CACHE_TTL_SEC
    with _lock:
        conn = _connect()
        cur = conn.execute("DELETE FROM cache WHERE cached_at < ?", (cutoff,))
        conn.commit()
        removed = cur.rowcount
        conn.close()
    log.info("Cache purged %d expired entries", removed)
    return removed


def invalidate(key: str) -> None:
    """Remove a specific cache entry."""
    with _lock:
        conn = _connect()
        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        conn.close()
    log.debug("Cache INVALIDATED key=%s", key)
