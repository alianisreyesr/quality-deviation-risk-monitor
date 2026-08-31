"""Tests for the sql/transformations.sql analytics views.

fact_deviation_events and fact_capa_lifecycle are applied automatically by
app/database.initialize_database() — these tests query them directly
against the live SQLite database used by the rest of the suite.
"""
from app.config import DATABASE_FILE
from app.database import connection


def _query(sql: str) -> list[dict]:
    with connection(DATABASE_FILE) as conn:
        return [dict(row) for row in conn.execute(sql)]


def test_fact_deviation_events_exists_and_has_rows():
    rows = _query("SELECT * FROM fact_deviation_events")
    assert len(rows) > 0


def test_fact_deviation_events_row_count_matches_source_table():
    fact_rows = _query("SELECT COUNT(*) AS n FROM fact_deviation_events")[0]["n"]
    source_rows = _query("SELECT COUNT(*) AS n FROM deviations")[0]["n"]
    assert fact_rows == source_rows


def test_fact_deviation_events_derived_columns_present():
    row = _query("SELECT * FROM fact_deviation_events LIMIT 1")[0]
    for column in ("severity_weight", "is_unassigned", "is_closed", "is_overdue", "days_open"):
        assert column in row


def test_fact_deviation_events_closed_records_have_no_days_open():
    rows = _query("SELECT * FROM fact_deviation_events WHERE is_closed = 1")
    for row in rows:
        assert row["days_open"] is None
        assert row["is_overdue"] == 0


def test_fact_deviation_events_severity_weight_matches_scoring():
    rows = _query("SELECT severity, severity_weight FROM fact_deviation_events")
    expected = {"High": 3, "Medium": 1, "Low": 0}
    for row in rows:
        assert row["severity_weight"] == expected[row["severity"]]


def test_fact_capa_lifecycle_exists_and_has_rows():
    rows = _query("SELECT * FROM fact_capa_lifecycle")
    assert len(rows) > 0


def test_fact_capa_lifecycle_row_count_matches_source_table():
    fact_rows = _query("SELECT COUNT(*) AS n FROM fact_capa_lifecycle")[0]["n"]
    source_rows = _query("SELECT COUNT(*) AS n FROM capas")[0]["n"]
    assert fact_rows == source_rows


def test_fact_capa_lifecycle_closed_records_have_days_open_to_close():
    rows = _query(
        "SELECT * FROM fact_capa_lifecycle WHERE is_closed = 1 AND closure_date IS NOT NULL"
    )
    assert rows, "Expected at least one closed CAPA with a closure_date"
    for row in rows:
        assert row["days_open"] is not None
        assert row["days_open"] >= 0
        assert row["is_overdue"] == 0


def test_fact_capa_lifecycle_root_cause_bucket_defaults_to_unspecified():
    rows = _query(
        "SELECT root_cause, root_cause_bucket FROM fact_capa_lifecycle WHERE root_cause IS NULL"
    )
    for row in rows:
        assert row["root_cause_bucket"] == "Unspecified"


def test_fact_capa_lifecycle_closed_without_effectiveness_check_flag():
    rows = _query(
        "SELECT status, effectiveness_check_complete, closed_without_effectiveness_check "
        "FROM fact_capa_lifecycle"
    )
    for row in rows:
        expected = row["status"] == "Closed" and not row["effectiveness_check_complete"]
        assert bool(row["closed_without_effectiveness_check"]) == expected
