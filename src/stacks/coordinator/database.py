"""
SQLite database setup and connection management for the download queue.

Uses WAL mode for concurrent read/write access from multiple processes.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime

from stacks.constants import CONFIG_PATH, QUEUE_FILE

logger = logging.getLogger(__name__)

# Database file path
DATABASE_PATH = CONFIG_PATH / "queue.db"

# Database schema
SCHEMA_SQL = """
-- Downloads table (replaces queue.json)
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    md5 TEXT NOT NULL UNIQUE,
    title TEXT,
    source TEXT,
    subfolder TEXT,
    status TEXT NOT NULL DEFAULT 'pending_scrape',
    added_at TEXT NOT NULL,
    completed_at TEXT,

    -- Scraper populates these
    filename TEXT,
    mirrors TEXT,  -- JSON array of mirror objects

    -- Worker assignment
    assigned_worker TEXT,
    assigned_mirror TEXT,  -- JSON object: {url, domain, type}

    -- Result info
    success INTEGER,  -- 0 or 1
    filepath TEXT,
    error TEXT,
    used_fast_download INTEGER DEFAULT 0,  -- 0 or 1

    -- Worker control commands (set by API, read by worker)
    -- Values: NULL, 'cancel_requeue', 'cancel_remove'
    command TEXT,

    -- Live progress reported by the worker (JSON)
    -- {percent, downloaded, total_size, speed}
    progress TEXT,

    -- Tracking
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status);
CREATE INDEX IF NOT EXISTS idx_downloads_md5 ON downloads(md5);
CREATE INDEX IF NOT EXISTS idx_downloads_added_at ON downloads(added_at);

-- Busy mirrors table (tracks which mirrors are currently in use)
CREATE TABLE IF NOT EXISTS busy_mirrors (
    domain TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL,
    claimed_at TEXT NOT NULL
);

-- Worker heartbeats (for health monitoring)
CREATE TABLE IF NOT EXISTS worker_heartbeats (
    worker_id TEXT PRIMARY KEY,
    worker_type TEXT NOT NULL,  -- 'download', 'scraper', 'coordinator'
    last_seen TEXT NOT NULL,
    current_download_id INTEGER
);

-- Migration tracking table
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL
);

-- System-wide flags (pause state, etc.)
CREATE TABLE IF NOT EXISTS system_flags (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    """
    Get a database connection with WAL mode enabled.

    Each call returns a new connection. Caller is responsible for closing it.
    WAL mode allows concurrent readers while one writer is active.

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row
    """
    # Ensure directory exists
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DATABASE_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout for locks
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """
    Initialize the database schema.

    Creates all tables if they don't exist. Safe to call multiple times.
    """
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)

        # Add columns to existing databases that predate them
        for col_def in [
            "ALTER TABLE downloads ADD COLUMN command TEXT",
            "ALTER TABLE downloads ADD COLUMN progress TEXT",
        ]:
            try:
                conn.execute(col_def)
                conn.commit()
            except Exception:
                pass  # Column already exists

        conn.commit()
        logger.info(f"Database initialized at {DATABASE_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        conn.close()


def startup_cleanup():
    """
    Clear stale state left over from a previous run.

    Called once at startup before any workers are spawned.  Since no workers
    are running yet, it is safe to:
    - Drop all busy_mirror locks (workers from the last run are gone)
    - Reset any 'downloading' jobs back to 'queued' (nobody is processing them)
    - Clear stale worker heartbeats
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM busy_mirrors")
        conn.execute("DELETE FROM worker_heartbeats")

        # Honor any pending cancel_remove commands from the previous run
        conn.execute("""
            DELETE FROM downloads
            WHERE status = 'downloading' AND command = 'cancel_remove'
        """)

        conn.execute("""
            UPDATE downloads
            SET status = 'queued',
                assigned_worker = NULL,
                assigned_mirror = NULL,
                command = NULL,
                progress = NULL
            WHERE status = 'downloading'
        """)
        conn.execute("""
            UPDATE downloads
            SET status = 'pending_scrape',
                assigned_worker = NULL
            WHERE status = 'scraping'
        """)
        conn.commit()
        logger.info("Startup cleanup: cleared stale locks and reset orphaned jobs")
    except Exception as e:
        logger.error(f"Startup cleanup failed: {e}")
        conn.rollback()
    finally:
        conn.close()


def migrate_from_json():
    """
    One-time migration from queue.json to SQLite.

    Imports existing queue items and history from queue.json if:
    - queue.json exists
    - Migration hasn't been applied yet

    After migration, queue.json is renamed to queue.json.migrated as backup.
    """
    conn = get_connection()
    try:
        # Check if migration already applied
        cursor = conn.execute(
            "SELECT 1 FROM migrations WHERE name = 'queue_json_import'"
        )
        if cursor.fetchone():
            logger.debug("queue.json migration already applied")
            return

        # Check if queue.json exists
        queue_file = Path(QUEUE_FILE)
        if not queue_file.exists():
            logger.debug("No queue.json found, skipping migration")
            # Mark migration as done anyway
            conn.execute(
                "INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
                ('queue_json_import', datetime.now().isoformat())
            )
            conn.commit()
            return

        # Load queue.json
        logger.info(f"Migrating from {queue_file}")
        with open(queue_file, 'r') as f:
            data = json.load(f)

        queue_items = data.get('queue', [])
        history_items = data.get('history', [])

        # Import queue items
        for item in queue_items:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO downloads
                    (md5, source, subfolder, status, added_at)
                    VALUES (?, ?, ?, 'pending_scrape', ?)
                """, (
                    item.get('md5'),
                    item.get('source'),
                    item.get('subfolder'),
                    item.get('added_at', datetime.now().isoformat())
                ))
            except Exception as e:
                logger.warning(f"Failed to migrate queue item {item.get('md5')}: {e}")

        # Import history items
        for item in history_items:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO downloads
                    (md5, filename, source, subfolder, status, added_at, completed_at,
                     success, filepath, error, used_fast_download)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('md5'),
                    item.get('filename'),
                    'migrated',
                    item.get('subfolder'),
                    'completed' if item.get('success') else 'failed',
                    item.get('completed_at', datetime.now().isoformat()),  # Use completed_at as added_at
                    item.get('completed_at'),
                    1 if item.get('success') else 0,
                    item.get('filepath'),
                    item.get('error'),
                    1 if item.get('used_fast_download') else 0
                ))
            except Exception as e:
                logger.warning(f"Failed to migrate history item {item.get('md5')}: {e}")

        # Mark migration as done
        conn.execute(
            "INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
            ('queue_json_import', datetime.now().isoformat())
        )
        conn.commit()

        # Backup queue.json
        backup_path = queue_file.with_suffix('.json.migrated')
        queue_file.rename(backup_path)
        logger.info(f"Migration complete: {len(queue_items)} queue items, {len(history_items)} history items")
        logger.info(f"Original queue.json backed up to {backup_path}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a dictionary."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows) -> list:
    """Convert an iterable of sqlite3.Row to a list of dictionaries."""
    return [dict(row) for row in rows]
