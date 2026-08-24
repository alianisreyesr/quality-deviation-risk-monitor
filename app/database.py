"""Database layer — synchronous (sqlite3) and asynchronous (aiosqlite) helpers.

Sync functions are used by the startup lifespan and legacy code paths.
Async functions are available for future async endpoint migration.
"""

import csv
import sqlite3
from pathlib import Path

import aiosqlite

from app.config import DATA_FILE, DATABASE_FILE, SCHEMA_FILE
from app.logger import setup_logger

logger = setup_logger(__name__)

# CSV / legacy labels → reviewer-workflow vocabulary used by audit_router.
REVIEW_STATUS_MAP = {
    "Not Started": "Open",
    "Pending Review": "Open",
    "In Review": "Under Review",
    "Escalated": "Investigation In Progress",
    "Open": "Open",
    "Under Review": "Under Review",
    "Investigation In Progress": "Investigation In Progress",
    "Closed": "Closed",
}


def _normalize_review_status(value: str) -> str:
    mapped = REVIEW_STATUS_MAP.get(str(value).strip())
    if mapped is None:
        raise ValueError(f"Unknown review_status {value!r}")
    return mapped


# ---------------------------------------------------------------------------
# Synchronous helpers (sqlite3)
# ---------------------------------------------------------------------------

def connection(database_file: Path = DATABASE_FILE) -> sqlite3.Connection:
    """Create and return a synchronous database connection."""
    try:
        database_file.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(database_file)
        conn.row_factory = sqlite3.Row
        logger.debug(f"Database connection established to {database_file}")
        return conn
    except sqlite3.DatabaseError as e:
        logger.error(f"Failed to connect to database at {database_file}: {e}")
        raise


def initialize_database(database_file: Path = DATABASE_FILE) -> None:
    """Initialize database schema and seed data.

    Raises:
        FileNotFoundError: If schema or data files are missing.
        sqlite3.DatabaseError: If database operations fail.
    """
    try:
        if not SCHEMA_FILE.exists():
            raise FileNotFoundError(f"Schema file not found at {SCHEMA_FILE}")
        if not DATA_FILE.exists():
            raise FileNotFoundError(f"Data file not found at {DATA_FILE}")

        logger.info("Initializing database schema and data...")

        with connection(database_file) as conn:
            conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
            existing = conn.execute("SELECT COUNT(*) FROM deviations").fetchone()[0]

            if existing:
                logger.info(f"Database already contains {existing} records")
                return

            logger.info("Seeding database from CSV...")
            with DATA_FILE.open(newline="", encoding="utf-8") as source:
                rows = list(csv.DictReader(source))

            if not rows:
                logger.warning("CSV file is empty")
                return

            for row in rows:
                row["review_status"] = _normalize_review_status(row.get("review_status", ""))

            conn.executemany(
                """
                INSERT INTO deviations (
                    deviation_id, title, severity, opened_date, due_date,
                    investigation_owner, repeat_occurrence, record_complete,
                    review_status
                ) VALUES (
                    :deviation_id, :title, :severity, :opened_date, :due_date,
                    NULLIF(:investigation_owner, ''), :repeat_occurrence,
                    :record_complete, :review_status
                )
                """,
                rows,
            )
            conn.commit()
            logger.info(f"Successfully seeded {len(rows)} records into database")

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        raise
    except sqlite3.DatabaseError as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise


def reset_database(database_file: Path = DATABASE_FILE) -> None:
    """Recreate the local SQLite database from the synthetic CSV."""
    if database_file.exists():
        database_file.unlink()
    initialize_database(database_file)


def fetch_deviations(database_file: Path = DATABASE_FILE) -> list[dict[str, object]]:
    """Fetch all deviation records (synchronous)."""
    try:
        with connection(database_file) as conn:
            rows = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM deviations ORDER BY due_date, deviation_id"
                )
            ]
        logger.debug(f"Retrieved {len(rows)} deviations from database")
        return rows
    except sqlite3.DatabaseError as e:
        logger.error(f"Failed to fetch deviations: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching deviations: {e}")
        raise


# ---------------------------------------------------------------------------
# Asynchronous helpers (aiosqlite)
# ---------------------------------------------------------------------------

async def async_connection(
    database_file: Path = DATABASE_FILE,
) -> aiosqlite.Connection:
    """Open and return an async aiosqlite connection.

    The caller is responsible for closing the connection (use as async context
    manager or call ``await conn.close()``).
    """
    database_file.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(database_file)
    conn.row_factory = aiosqlite.Row
    logger.debug(f"Async database connection established to {database_file}")
    return conn


async def async_fetch_deviations(
    database_file: Path = DATABASE_FILE,
) -> list[dict[str, object]]:
    """Fetch all deviation records asynchronously.

    Intended for future async endpoint migration.  Functionally equivalent
    to ``fetch_deviations`` but non-blocking.
    """
    try:
        async with await async_connection(database_file) as conn:
            async with conn.execute(
                "SELECT * FROM deviations ORDER BY due_date, deviation_id"
            ) as cursor:
                rows = [dict(row) async for row in cursor]
        logger.debug(f"Async retrieved {len(rows)} deviations from database")
        return rows
    except Exception as e:
        logger.error(f"Async fetch_deviations failed: {e}")
        raise
