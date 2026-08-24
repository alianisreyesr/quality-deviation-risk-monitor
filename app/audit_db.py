"""Database helpers for the append-only audit_log table."""

import sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.config import DATABASE_FILE
from app.logger import setup_logger

logger = setup_logger(__name__)

CREATE_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    deviation_id    TEXT,
    action          TEXT    NOT NULL,
    actor           TEXT    NOT NULL DEFAULT 'unknown',
    comment         TEXT,
    previous_status TEXT,
    new_status      TEXT,
    previous_value  TEXT,
    new_value       TEXT,
    reason          TEXT,
    correlation_id  TEXT,
    ip_address      TEXT,
    user_agent      TEXT,
    status_code     INTEGER,
    latency_ms      REAL,
    created_at      TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_log_correlation_id
ON audit_log(correlation_id);
"""

MIGRATABLE_COLUMNS = {
    "previous_value": "TEXT",
    "new_value": "TEXT",
    "reason": "TEXT",
    "correlation_id": "TEXT",
}


def _migrate_audit_log(conn: sqlite3.Connection) -> None:
    """Add event-context columns for databases created before this schema."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(audit_log)")}
    for name, definition in MIGRATABLE_COLUMNS.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE audit_log ADD COLUMN {name} {definition}")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_log_correlation_id "
        "ON audit_log(correlation_id)"
    )


def initialize_audit_table() -> None:
    """Create or migrate audit_log without modifying historical events."""
    try:
        from app.database import connection
        with connection(DATABASE_FILE) as conn:
            conn.executescript(CREATE_AUDIT_TABLE)
            _migrate_audit_log(conn)
            conn.commit()
        logger.info("audit_log table ready")
    except sqlite3.DatabaseError as exc:
        logger.error(f"Failed to initialize audit_log table: {exc}")
        raise


def insert_audit_event(
    action: str,
    actor: str,
    *,
    deviation_id: str | None = None,
    comment: str | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
    previous_value: str | None = None,
    new_value: str | None = None,
    reason: str | None = None,
    correlation_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status_code: int | None = None,
    latency_ms: float | None = None,
) -> int:
    """Insert one immutable event with a generated correlation ID when absent."""
    created_at = datetime.now(timezone.utc).isoformat()
    event_correlation_id = correlation_id or str(uuid4())
    event_reason = reason if reason is not None else comment
    event_previous_value = previous_value if previous_value is not None else previous_status
    event_new_value = new_value if new_value is not None else new_status
    try:
        from app.database import connection
        with connection(DATABASE_FILE) as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_log (
                    deviation_id, action, actor, comment,
                    previous_status, new_status,
                    previous_value, new_value, reason, correlation_id,
                    ip_address, user_agent, status_code, latency_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    deviation_id, action, actor, comment,
                    previous_status, new_status,
                    event_previous_value, event_new_value, event_reason, event_correlation_id,
                    ip_address, user_agent, status_code, latency_ms, created_at,
                ),
            )
            conn.commit()
            logger.debug(
                f"Audit event #{cursor.lastrowid} recorded: {action} by {actor} "
                f"correlation_id={event_correlation_id}"
            )
            return cursor.lastrowid  # type: ignore[return-value]
    except sqlite3.DatabaseError as exc:
        logger.error(f"Failed to insert audit event: {exc}")
        raise


def fetch_audit_log(
    deviation_id: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Fetch audit log entries, newest first."""
    try:
        from app.database import connection
        with connection(DATABASE_FILE) as conn:
            if deviation_id:
                rows = conn.execute(
                    "SELECT * FROM audit_log WHERE deviation_id = ? ORDER BY id DESC LIMIT ?",
                    (deviation_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.DatabaseError as exc:
        logger.error(f"Failed to fetch audit log: {exc}")
        raise


def fetch_deviation_current_status(deviation_id: str) -> str | None:
    """Fetch a deviation status without modifying it."""
    try:
        from app.database import connection
        with connection(DATABASE_FILE) as conn:
            row = conn.execute(
                "SELECT review_status FROM deviations WHERE deviation_id = ?",
                (deviation_id,),
            ).fetchone()
        return row["review_status"] if row else None
    except sqlite3.DatabaseError as exc:
        logger.error(f"Failed to fetch status for deviation {deviation_id}: {exc}")
        raise


def update_deviation_status(deviation_id: str, new_status: str) -> str | None:
    """Update review_status and return its previous value."""
    try:
        from app.database import connection
        with connection(DATABASE_FILE) as conn:
            row = conn.execute(
                "SELECT review_status FROM deviations WHERE deviation_id = ?",
                (deviation_id,),
            ).fetchone()
            if row is None:
                return None
            previous = row["review_status"]
            conn.execute(
                "UPDATE deviations SET review_status = ? WHERE deviation_id = ?",
                (new_status, deviation_id),
            )
            conn.commit()
        logger.info(f"Deviation {deviation_id} status: {previous} → {new_status}")
        return previous
    except sqlite3.DatabaseError as exc:
        logger.error(f"Failed to update deviation status: {exc}")
        raise
