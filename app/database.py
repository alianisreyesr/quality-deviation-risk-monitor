import csv
import sqlite3
from pathlib import Path

from app.config import DATA_FILE, DATABASE_FILE, SCHEMA_FILE


def connection(database_file: Path = DATABASE_FILE) -> sqlite3.Connection:
    database_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_file)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(database_file: Path = DATABASE_FILE) -> None:
    with connection(database_file) as conn:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        existing = conn.execute("SELECT COUNT(*) FROM deviations").fetchone()[0]
        if existing:
            return
        with DATA_FILE.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        conn.executemany(
            """INSERT INTO deviations (deviation_id, title, severity, opened_date, due_date, investigation_owner, repeat_occurrence, record_complete, review_status) VALUES (:deviation_id, :title, :severity, :opened_date, :due_date, NULLIF(:investigation_owner, ''), :repeat_occurrence, :record_complete, :review_status)""",
            rows,
        )


def fetch_deviations(database_file: Path = DATABASE_FILE) -> list[dict[str, object]]:
    with connection(database_file) as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM deviations ORDER BY due_date, deviation_id")]
