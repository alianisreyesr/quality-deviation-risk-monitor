#!/usr/bin/env python3
"""
scripts/load_data.py

Staging script for Quality Deviation Risk Monitor.
Loads synthetic CSV data into a SQLite database using the schema defined in
sql/schema.sql, following the pipeline documented in the README:

    Synthetic CSV → SQLite staging table → validation + risk rules → FastAPI endpoints

References:
  - ALCOA+ (Attributable, Legible, Contemporaneous, Original, Accurate)
  - 21 CFR Part 11 §11.10(e): audit trail for data integrity
  - ICH Q10 §3.2: deviation record completeness

Usage:
    python scripts/load_data.py                   # loads data/deviations.csv into deviations.db
    python scripts/load_data.py --csv path/to.csv # loads a custom CSV file
    python scripts/load_data.py --db path/to.db   # writes to a custom DB path
    python scripts/load_data.py --dry-run         # validates CSV without writing to DB
"""

import argparse
import csv
import logging
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = PROJECT_ROOT / "data" / "deviations.csv"
DEFAULT_DB  = PROJECT_ROOT / "deviations.db"
SCHEMA_SQL  = PROJECT_ROOT / "sql" / "schema.sql"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Validation constants (ALCOA+ field-level checks)
# ---------------------------------------------------------------------------
VALID_SEVERITIES   = {"Low", "Medium", "High"}
VALID_BOOL_STRINGS = {"true", "false"}
DATE_FORMAT        = "%Y-%m-%d"

REQUIRED_FIELDS = [
    "deviation_id", "title", "severity",
    "opened_date", "due_date", "review_status",
]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def _parse_date(value: str, field: str, row_id: str) -> str | None:
    """Return ISO date string or None; log a warning on parse failure."""
    try:
        datetime.strptime(value.strip(), DATE_FORMAT)
        return value.strip()
    except ValueError:
        log.warning("Row %s — field '%s' has invalid date '%s'; expected YYYY-MM-DD", row_id, field, value)
        return None


def _parse_bool(value: str, field: str, row_id: str) -> int | None:
    """Convert 'True'/'False' CSV strings to SQLite INTEGER (1/0)."""
    normalised = value.strip().lower()
    if normalised not in VALID_BOOL_STRINGS:
        log.warning("Row %s — field '%s' has unexpected value '%s'; expected True/False", row_id, field, value)
        return None
    return 1 if normalised == "true" else 0


def validate_row(row: dict, row_num: int) -> list[str]:
    """
    ALCOA+ data integrity checks.
    Returns a list of violation strings (empty = record is clean).
    """
    errors = []
    row_id = row.get("deviation_id", f"<row {row_num}>")

    # 1. Required fields must be present and non-blank
    for field in REQUIRED_FIELDS:
        if not row.get(field, "").strip():
            errors.append(f"{row_id}: required field '{field}' is missing or blank")

    # 2. Severity must be a controlled vocabulary value
    sev = row.get("severity", "").strip()
    if sev and sev not in VALID_SEVERITIES:
        errors.append(f"{row_id}: severity '{sev}' is not in {VALID_SEVERITIES}")

    # 3. Date fields must be parseable ISO dates
    for date_field in ("opened_date", "due_date"):
        val = row.get(date_field, "").strip()
        if val and _parse_date(val, date_field, row_id) is None:
            errors.append(f"{row_id}: '{date_field}' value '{val}' is not a valid date")

    # 4. Boolean fields must be True/False
    for bool_field in ("repeat_occurrence", "record_complete"):
        val = row.get(bool_field, "").strip()
        if val and val.lower() not in VALID_BOOL_STRINGS:
            errors.append(f"{row_id}: '{bool_field}' value '{val}' must be True or False")

    # 5. Temporal consistency: opened_date must not be after due_date
    try:
        opened = date.fromisoformat(row.get("opened_date", "").strip())
        due    = date.fromisoformat(row.get("due_date", "").strip())
        if opened > due:
            errors.append(f"{row_id}: opened_date ({opened}) is after due_date ({due}) — check ALCOA Contemporaneous")
    except ValueError:
        pass  # Already flagged above

    return errors


# ---------------------------------------------------------------------------
# CSV → SQLite pipeline
# ---------------------------------------------------------------------------
def load_schema(conn: sqlite3.Connection) -> None:
    """Execute sql/schema.sql to create the deviations table if it doesn't exist."""
    if not SCHEMA_SQL.exists():
        log.error("Schema file not found: %s", SCHEMA_SQL)
        sys.exit(1)
    schema = SCHEMA_SQL.read_text(encoding="utf-8")
    conn.executescript(schema)
    log.info("Schema applied from %s", SCHEMA_SQL)


def read_csv(csv_path: Path) -> list[dict]:
    """Read and return all rows from the CSV file."""
    if not csv_path.exists():
        log.error("CSV file not found: %s", csv_path)
        sys.exit(1)
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    log.info("Read %d record(s) from %s", len(rows), csv_path)
    return rows


def validate_all(rows: list[dict]) -> bool:
    """
    Run ALCOA+ validation across all rows.
    Returns True if all records are clean, False if any violation was found.
    """
    all_errors: list[str] = []
    for i, row in enumerate(rows, start=2):  # row 1 = header
        errors = validate_row(row, i)
        all_errors.extend(errors)

    if all_errors:
        log.warning("Data validation found %d issue(s):", len(all_errors))
        for err in all_errors:
            log.warning("  ✗ %s", err)
        return False

    log.info("ALCOA+ validation passed — all %d record(s) are clean", len(rows))
    return True


def insert_rows(conn: sqlite3.Connection, rows: list[dict]) -> tuple[int, int]:
    """
    Insert rows into the deviations table using INSERT OR REPLACE.
    Returns (inserted, skipped) counts.
    """
    inserted = 0
    skipped  = 0

    cursor = conn.cursor()
    for row in rows:
        row_id = row.get("deviation_id", "").strip()

        # Parse booleans to integers (SQLite CHECK expects 0/1)
        repeat = _parse_bool(row.get("repeat_occurrence", ""), "repeat_occurrence", row_id)
        complete = _parse_bool(row.get("record_complete", ""), "record_complete", row_id)

        if repeat is None or complete is None:
            log.warning("Skipping row %s due to unparseable boolean field(s)", row_id)
            skipped += 1
            continue

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO deviations (
                    deviation_id, title, severity, opened_date, due_date,
                    investigation_owner, repeat_occurrence, record_complete, review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    row.get("title", "").strip(),
                    row.get("severity", "").strip(),
                    row.get("opened_date", "").strip(),
                    row.get("due_date", "").strip(),
                    row.get("investigation_owner", "").strip() or None,
                    repeat,
                    complete,
                    row.get("review_status", "").strip(),
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError as exc:
            log.warning("Skipping row %s — integrity error: %s", row_id, exc)
            skipped += 1

    conn.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Audit log helper (21 CFR Part 11 §11.10(e))
# ---------------------------------------------------------------------------
def log_audit_entry(conn: sqlite3.Connection, csv_path: Path, inserted: int, skipped: int) -> None:
    """
    Write a lightweight audit entry to a load_audit table so reviewers can trace
    every staging run back to its source file and timestamp (21 CFR Part 11 §11.10(e)).
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS load_audit (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            loaded_at   TEXT NOT NULL,
            source_file TEXT NOT NULL,
            rows_loaded INTEGER NOT NULL,
            rows_skipped INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO load_audit (loaded_at, source_file, rows_loaded, rows_skipped) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat() + "Z", str(csv_path.resolve()), inserted, skipped),
    )
    conn.commit()
    log.info("Audit entry written (21 CFR Part 11 §11.10(e)): %d loaded, %d skipped", inserted, skipped)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load synthetic deviation CSV into SQLite (Quality Deviation Risk Monitor)"
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to input CSV file")
    parser.add_argument("--db",  type=Path, default=DEFAULT_DB,  help="Path to SQLite database file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the CSV without writing to the database",
    )
    args = parser.parse_args()

    log.info("=== Quality Deviation Risk Monitor — Staging Pipeline ===")
    log.info("Source : %s", args.csv)
    log.info("Target : %s", args.db)
    if args.dry_run:
        log.info("Mode   : DRY RUN (no DB writes)")

    # 1. Read CSV
    rows = read_csv(args.csv)

    # 2. ALCOA+ validation
    clean = validate_all(rows)
    if not clean:
        log.warning("Validation issues found. Proceeding with clean rows; problematic rows will be skipped.")

    if args.dry_run:
        log.info("Dry run complete — no database written.")
        sys.exit(0 if clean else 1)

    # 3. Connect to SQLite and apply schema
    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA journal_mode=WAL")  # Write-ahead log for concurrency safety
    conn.execute("PRAGMA foreign_keys=ON")

    load_schema(conn)

    # 4. Insert rows
    inserted, skipped = insert_rows(conn, rows)
    log.info("Loaded: %d inserted, %d skipped", inserted, skipped)

    # 5. Audit log
    log_audit_entry(conn, args.csv, inserted, skipped)

    conn.close()
    log.info("Database written to %s", args.db)
    log.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
