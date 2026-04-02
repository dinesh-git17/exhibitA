"""SQLite database lifecycle, WAL enforcement, and schema bootstrap."""

import sqlite3
from pathlib import Path

import aiosqlite

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS content (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('contract', 'letter', 'thought')),
    title TEXT,
    subtitle TEXT,
    body TEXT NOT NULL,
    article_number TEXT,
    classification TEXT,
    section_order INTEGER NOT NULL,
    requires_signature BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS signatures (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES content(id),
    signer TEXT NOT NULL CHECK(signer IN ('dinesh', 'carolina')),
    image BLOB NOT NULL,
    signed_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(content_id, signer)
);

CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES content(id),
    signer TEXT NOT NULL CHECK(signer IN ('dinesh', 'carolina')),
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(content_id, signer)
);

CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('create', 'update', 'delete')),
    occurred_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS device_tokens (
    id TEXT PRIMARY KEY,
    signer TEXT NOT NULL CHECK(signer IN ('dinesh', 'carolina')),
    token TEXT NOT NULL UNIQUE,
    registered_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    signer TEXT NOT NULL UNIQUE CHECK(signer IN ('dinesh', 'carolina')),
    key_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS admin_sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS filings (
    id TEXT PRIMARY KEY,
    filing_type TEXT NOT NULL
        CHECK(filing_type IN ('motion', 'objection', 'emergency_order')),
    filed_by TEXT NOT NULL CHECK(filed_by IN ('dinesh', 'carolina')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    ruling TEXT CHECK(ruling IN ('granted', 'denied', 'sustained', 'overruled')),
    ruling_reason TEXT,
    ruled_by TEXT CHECK(ruled_by IN ('dinesh', 'carolina')),
    ruled_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_INDEX_SQL = """\
CREATE INDEX IF NOT EXISTS idx_content_type ON content(type);
CREATE INDEX IF NOT EXISTS idx_content_order ON content(type, section_order);
CREATE INDEX IF NOT EXISTS idx_signatures_content ON signatures(content_id);
CREATE INDEX IF NOT EXISTS idx_comments_content ON comments(content_id);
CREATE INDEX IF NOT EXISTS idx_sync_log_time ON sync_log(occurred_at);
CREATE INDEX IF NOT EXISTS idx_filings_type ON filings(filing_type);
CREATE INDEX IF NOT EXISTS idx_filings_created ON filings(created_at DESC);
"""


async def connect(db_path: Path) -> aiosqlite.Connection:
    """Open a connection, enforce WAL mode, and bootstrap schema and indexes."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = await aiosqlite.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    await connection.execute("PRAGMA journal_mode=WAL")
    await connection.execute("PRAGMA busy_timeout=15000")
    await connection.execute("PRAGMA foreign_keys=ON")
    await connection.executescript(_SCHEMA_SQL)
    await connection.executescript(_INDEX_SQL)
    await connection.commit()
    return connection


async def checkpoint(connection: aiosqlite.Connection) -> None:
    """Run a passive WAL checkpoint to compact the write-ahead log.

    Passive checkpoints transfer WAL pages back to the main database
    without requiring an exclusive lock, preventing unbounded WAL growth
    when Litestream holds a read lock for replication.
    """
    await connection.execute("PRAGMA wal_checkpoint(PASSIVE)")
