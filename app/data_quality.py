"""Data quality analysis helpers for the deviation dataset.

Analyses are run against the live SQLite dataset on demand.  Results are
not cached because data quality is expected to change as records are updated
and this endpoint is primarily diagnostic rather than high-frequency.

Field validation rules mirror the data dictionary in docs/data-dictionary.md.
Update both files together whenever field definitions change.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.database import fetch_capas, fetch_deviations
from app.logger import setup_logger

logger = setup_logger(__name__)

# Allowed categorical values — must match docs/data-dictionary.md
ALLOWED_SEVERITY = {"Low", "Medium", "High"}
ALLOWED_REVIEW_STATUS = {
    "Open",
    "Under Review",
    "Investigation In Progress",
    "Closed",
}
ALLOWED_CAPA_TYPE = {"Corrective", "Preventive"}
ALLOWED_CAPA_STATUS = {
    "Open",
    "In Progress",
    "Pending Effectiveness Check",
    "Closed",
}
BOOLEAN_VALUES = {"true", "false", "1", "0", "yes", "no", True, False}


def _is_null(value: Any) -> bool:
    """Return True if value is None or an empty/whitespace string."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _is_valid_date(value: Any) -> bool:
    """Return True if value is a date object or a valid ISO-8601 date string."""
    if isinstance(value, date):
        return True
    try:
        date.fromisoformat(str(value))
        return True
    except (ValueError, TypeError):
        return False


def _is_valid_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, str) and value.strip().lower() in {"true", "false", "1", "0", "yes", "no"}:
        return True
    return False


# ---------------------------------------------------------------------------
# Per-field validation predicates
# Each returns (is_null: bool, is_invalid: bool, display_value: str)
# ---------------------------------------------------------------------------

def _check_field(
    record: dict,
    field: str,
    *,
    required: bool = True,
    allowed_values: set | None = None,
    is_date: bool = False,
    is_bool: bool = False,
    max_length: int | None = None,
) -> tuple[bool, bool, str]:
    value = record.get(field)
    null = _is_null(value)
    if null:
        return True, False, ""

    invalid = False
    display = str(value)[:80]

    if allowed_values and str(value) not in allowed_values or is_date and not _is_valid_date(value) or is_bool and not _is_valid_bool(value) or max_length and len(str(value)) > max_length:
        invalid = True

    return False, invalid, display if invalid else ""


# Field spec: (field_name, check_kwargs)
FIELD_SPECS: list[tuple[str, dict]] = [
    ("deviation_id",       {"required": True,  "max_length": 50}),
    ("title",              {"required": True,  "max_length": 255}),
    ("severity",           {"required": True,  "allowed_values": ALLOWED_SEVERITY}),
    ("opened_date",        {"required": True,  "is_date": True}),
    ("due_date",           {"required": True,  "is_date": True}),
    ("investigation_owner",{"required": False}),          # nullable — unassigned is valid
    ("repeat_occurrence",  {"required": True,  "is_bool": True}),
    ("record_complete",    {"required": True,  "is_bool": True}),
    ("review_status",      {"required": True,  "allowed_values": ALLOWED_REVIEW_STATUS}),
]

# CAPA field spec — mirrors FIELD_SPECS. closure_date is intentionally
# nullable (only set once a CAPA closes); root_cause is nullable at the
# field-validation layer but its absence is still scored as a risk signal
# in app/capa_scoring.py.
CAPA_FIELD_SPECS: list[tuple[str, dict]] = [
    ("capa_id",                      {"required": True,  "max_length": 50}),
    ("title",                        {"required": True,  "max_length": 255}),
    ("capa_type",                    {"required": True,  "allowed_values": ALLOWED_CAPA_TYPE}),
    ("severity",                     {"required": True,  "allowed_values": ALLOWED_SEVERITY}),
    ("opened_date",                  {"required": True,  "is_date": True}),
    ("due_date",                     {"required": True,  "is_date": True}),
    ("closure_date",                 {"required": False, "is_date": True}),
    ("owner",                        {"required": False}),   # nullable — unassigned is valid
    ("root_cause",                   {"required": False}),   # nullable — flagged separately in scoring
    ("recurrence_flag",              {"required": True,  "is_bool": True}),
    ("effectiveness_check_complete", {"required": True,  "is_bool": True}),
    ("status",                       {"required": True,  "allowed_values": ALLOWED_CAPA_STATUS}),
]


def _find_duplicate_ids(records: list[dict], id_field: str) -> tuple[set[int], list[str]]:
    """Return (record indices, sample values) for any ID that appears more than once.

    Every record sharing a duplicated ID is flagged — not just the extras —
    because a duplicate primary key makes every copy ambiguous.
    """
    positions: dict[str, list[int]] = {}
    for i, record in enumerate(records):
        value = record.get(id_field)
        if _is_null(value):
            continue
        positions.setdefault(str(value), []).append(i)

    duplicate_indices: set[int] = set()
    samples: list[str] = []
    for value, indices in positions.items():
        if len(indices) > 1:
            duplicate_indices.update(indices)
            if len(samples) < 5:
                samples.append(value)
    return duplicate_indices, samples


def _build_report(records: list[dict], field_specs: list[tuple[str, dict]], id_field: str) -> dict:
    """Shared field-quality + duplicate-ID pass for any record type.

    Checks unique IDs, required fields, valid dates, and allowed categorical
    values (severity, status, etc.) per field_specs.
    """
    total = len(records)

    field_reports: list[dict] = []
    records_with_issue: set[int] = set()  # track by index

    for field_name, kwargs in field_specs:
        null_indices: list[int] = []
        invalid_indices: list[int] = []
        sample_invalids: list[str] = []

        for i, record in enumerate(records):
            is_null, is_invalid, display = _check_field(record, field_name, **kwargs)
            if is_null and kwargs.get("required", True):
                null_indices.append(i)
                records_with_issue.add(i)
            if is_invalid:
                invalid_indices.append(i)
                records_with_issue.add(i)
                if len(sample_invalids) < 5:
                    sample_invalids.append(display)

        if field_name == id_field:
            duplicate_indices, duplicate_samples = _find_duplicate_ids(records, id_field)
            for i in duplicate_indices:
                if i not in invalid_indices:
                    invalid_indices.append(i)
                records_with_issue.add(i)
            for value in duplicate_samples:
                if len(sample_invalids) >= 5:
                    break
                if value not in sample_invalids:
                    sample_invalids.append(value)

        null_count = len(null_indices)
        invalid_count = len(invalid_indices)
        field_reports.append({
            "field_name": field_name,
            "total_records": total,
            "null_count": null_count,
            "invalid_count": invalid_count,
            "null_rate": round(null_count / total, 4) if total else 0.0,
            "invalid_rate": round(invalid_count / total, 4) if total else 0.0,
            "sample_invalid_values": sample_invalids,
        })

    issue_count = len(records_with_issue)
    return {
        "total_records": total,
        "records_with_any_issue": issue_count,
        "issue_rate": round(issue_count / total, 4) if total else 0.0,
        "fields": field_reports,
    }


def build_data_quality_report(records: list[dict] | None = None) -> dict:
    """Build a data quality summary for the full deviation dataset.

    Checks unique deviation_id values, required fields, valid dates, and
    allowed severity/review_status values.

    Args:
        records: Pre-loaded records (optional; loads from DB if None).

    Returns:
        Dict compatible with DataQualityResponse.
    """
    if records is None:
        records = fetch_deviations()
    logger.info(f"Running data quality analysis on {len(records)} deviation records")
    return _build_report(records, FIELD_SPECS, id_field="deviation_id")


def build_capa_data_quality_report(records: list[dict] | None = None) -> dict:
    """Build a data quality summary for the full CAPA dataset.

    Checks unique capa_id values, required fields, valid dates, and allowed
    capa_type/severity/status values.

    Args:
        records: Pre-loaded records (optional; loads from DB if None).

    Returns:
        Dict compatible with DataQualityResponse.
    """
    if records is None:
        records = fetch_capas()
    logger.info(f"Running data quality analysis on {len(records)} CAPA records")
    return _build_report(records, CAPA_FIELD_SPECS, id_field="capa_id")
