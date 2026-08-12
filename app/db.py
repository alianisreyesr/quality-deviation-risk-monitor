import sqlite3
import csv
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "deviations.db"
CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "deviations.csv"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the schema and seed from CSV if the DB does not yet exist."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema)
        existing = conn.execute("SELECT COUNT(*) FROM deviations").fetchone()[0]
        if existing == 0:
            _seed_from_csv(conn)


def _seed_from_csv(conn: sqlite3.Connection) -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row["deviation_id"],
                row["title"],
                row["severity"],
                row["opened_date"],
                row["due_date"],
                row["investigation_owner"].strip() or None,
                1 if row["repeat_occurrence"].strip().lower() == "true" else 0,
                1 if row["record_complete"].strip().lower() == "true" else 0,
                row["review_status"],
            )
            for row in reader
        ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO deviations
        (deviation_id, title, severity, opened_date, due_date,
         investigation_owner, repeat_occurrence, record_complete, review_status)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    conn.commit()


def fetch_all_deviations() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM deviations").fetchall()
    return [dict(row) for row in rows]
