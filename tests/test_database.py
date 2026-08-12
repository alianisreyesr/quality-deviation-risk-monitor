import csv

from app.config import DATA_FILE
from app.database import connection, fetch_deviations, initialize_database, reset_database


def synthetic_record_count() -> int:
    with DATA_FILE.open(newline="", encoding="utf-8") as source:
        return sum(1 for _ in csv.DictReader(source))


def test_reset_database_rebuilds_synthetic_records(tmp_path):
    database_file = tmp_path / "quality_monitor.db"
    expected_count = synthetic_record_count()

    initialize_database(database_file)
    with connection(database_file) as conn:
        conn.execute("DELETE FROM deviations WHERE deviation_id = (SELECT deviation_id FROM deviations LIMIT 1)")

    assert len(fetch_deviations(database_file)) == expected_count - 1

    reset_database(database_file)

    records = fetch_deviations(database_file)
    assert len(records) == expected_count
    assert {record["deviation_id"] for record in records}


def test_reset_database_is_idempotent(tmp_path):
    database_file = tmp_path / "quality_monitor.db"

    reset_database(database_file)
    first_run = fetch_deviations(database_file)
    reset_database(database_file)
    second_run = fetch_deviations(database_file)

    assert second_run == first_run
