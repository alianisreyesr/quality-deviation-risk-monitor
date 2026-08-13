"""Database helpers for the audit_log table.

Design constraints (21 CFR Part 11 / ALCOA+):
- audit_log rows are NEVER updated or deleted — append-only
- created_at is set server-side in UTC and stored as ISO-8601 text
- Separate from database.py to avoid circular imports with audit_router
"""

import sqlite3
from datetime import datetime, timezone
from typing import Any

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
    ip_address      TEXT,
    user_agent      TEXT,
    status_code     INTEGER,
    latency_ms      REAL,
    created_at      TEXT    NOT NULL
);
"""


def initialize_audit_table() -> None:
    """Create audit_log table if it does not already exist."""
    try:
        from app.database import connection  # local import — avoids circular
        with connection(DATABASE_FILE) as conn:
            conn.executescript(CREATE_AUDIT_TABLE)
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
    ip_address: str | None = None,
    user_agent: str | None = None,
    status_code: int | None = None,
    latency_ms: float | None = None,
) -> int:
    """Insert one immutable audit event row.

    Returns:
        The rowid of the newly inserted row.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        from app.database import connection  # local import
        with connection(DATABASE_FILE) as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_log (
                    deviation_id, action, actor, comment,
                    previous_status, new_status,
                    ip_address, user_agent,
                    status_code, latency_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    deviation_id, action, actor, comment,
                    previous_status, new_status,
                    ip_address, user_agent,
                    status_code, latency_ms, created_at,
                ),
            )
            conn.commit()
            logger.debug(f"Audit event #{cursor.lastrowid} recorded: {action} by {actor}")
            return cursor.lastrowid  # type: ignore[return-value]
    except sqlite3.DatabaseError as exc:
        logger.error(f"Failed to insert audit event: {exc}")
        raise


def fetch_audit_log(
    deviation_id: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Fetch audit log entries, newest first.

    Args:
        deviation_id: Optional filter — return only events for this deviation.
        limit: Maximum rows to return (default 500, max enforced by caller).

    Returns:
        List of audit event dicts.
    """
    try:
        from app.database import connection  # local import
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


def update_deviation_status(deviation_id: str, new_status: str) -> str | None:
    """Update review_status on a deviation row.

    Returns:
        The previous status before the update, or None if deviation not found.
    """
    try:
        from app.database import connection  # local import
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
