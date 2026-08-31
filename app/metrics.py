"""Quality metrics aggregated across deviations and CAPA records.

GET /metrics (via app/metrics_router.py) surfaces these numbers for a
dashboard (Metabase or otherwise — see docs/dashboard.md) without requiring
a caller to pull every raw record and recompute them client-side.

Metrics covered:
    - Aging       — how long records have been open (deviations and CAPA)
    - Recurrence  — share of records flagged as repeat/recurring
    - Severity    — distribution across Low / Medium / High
    - CAPA closure— closure rate, effectiveness-check rate, time-to-close
    - Root causes — CAPA breakdown by root_cause category

All figures are computed on-demand from the live SQLite dataset, matching
the diagnostic (not cached, not validated-GxP) posture of app/data_quality.py.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.capa_scoring import (
    AGING_TIER_CRITICAL_DAYS,
    AGING_TIER_ELEVATED_DAYS,
    compute_aging_days,
)
from app.database import fetch_capas, fetch_deviations
from app.logger import setup_logger
from app.scoring import as_bool

logger = setup_logger(__name__)

# Aging buckets for deviations mirror the CAPA tiers so both record types
# are reported on the same aging scale, even though deviation risk_score
# itself does not include an aging component (see docs/risk-rules.md).
DEVIATION_AGING_TIER_ELEVATED_DAYS = AGING_TIER_ELEVATED_DAYS
DEVIATION_AGING_TIER_CRITICAL_DAYS = AGING_TIER_CRITICAL_DAYS


def _to_date(value: object) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _age_bucket(days: int, elevated: int, critical: int) -> str:
    if days > critical:
        return f"> {critical}d"
    if days > elevated:
        return f"{elevated + 1}-{critical}d"
    return f"0-{elevated}d"


def _empty_aging_summary() -> dict[str, Any]:
    return {"open_count": 0, "avg_days_open": 0.0, "max_days_open": 0, "buckets": {}}


def build_deviation_aging_metric(
    records: list[dict] | None = None, today: date | None = None
) -> dict[str, Any]:
    """Aging summary for deviations still open (review_status != Closed).

    Deviations have no closure_date column, so aging is only meaningful
    while a record is open — closed deviations are excluded, matching how
    CAPA aging freezes at closure instead of continuing to grow.
    """
    today = today or date.today()
    records = records if records is not None else fetch_deviations()

    ages = [
        max((today - _to_date(r["opened_date"])).days, 0)
        for r in records
        if str(r.get("review_status")) != "Closed"
    ]
    if not ages:
        return _empty_aging_summary()

    buckets: dict[str, int] = {}
    for age in ages:
        bucket = _age_bucket(age, DEVIATION_AGING_TIER_ELEVATED_DAYS, DEVIATION_AGING_TIER_CRITICAL_DAYS)
        buckets[bucket] = buckets.get(bucket, 0) + 1

    return {
        "open_count": len(ages),
        "avg_days_open": round(sum(ages) / len(ages), 1),
        "max_days_open": max(ages),
        "buckets": buckets,
    }


def build_capa_aging_metric(
    records: list[dict] | None = None, today: date | None = None
) -> dict[str, Any]:
    """Aging summary for CAPA records still open (status != Closed).

    Reuses app.capa_scoring.compute_aging_days so this metric always agrees
    with the aging_days returned by GET /capas.
    """
    today = today or date.today()
    records = records if records is not None else fetch_capas()

    ages = [
        compute_aging_days(r, today)
        for r in records
        if str(r.get("status")) != "Closed"
    ]
    if not ages:
        return _empty_aging_summary()

    buckets: dict[str, int] = {}
    for age in ages:
        bucket = _age_bucket(age, AGING_TIER_ELEVATED_DAYS, AGING_TIER_CRITICAL_DAYS)
        buckets[bucket] = buckets.get(bucket, 0) + 1

    return {
        "open_count": len(ages),
        "avg_days_open": round(sum(ages) / len(ages), 1),
        "max_days_open": max(ages),
        "buckets": buckets,
    }


def build_recurrence_metric(
    deviation_records: list[dict], capa_records: list[dict]
) -> dict[str, float]:
    """Share of records flagged as a repeat occurrence / recurring root cause."""
    dev_total = len(deviation_records)
    dev_repeat = sum(1 for r in deviation_records if as_bool(r.get("repeat_occurrence")))
    capa_total = len(capa_records)
    capa_recurring = sum(1 for r in capa_records if as_bool(r.get("recurrence_flag")))
    return {
        "deviation_recurrence_rate": round(dev_repeat / dev_total, 4) if dev_total else 0.0,
        "capa_recurrence_rate": round(capa_recurring / capa_total, 4) if capa_total else 0.0,
    }


def build_severity_distribution(records: list[dict]) -> dict[str, int]:
    """Count of records per severity tier (Low / Medium / High)."""
    counts = {"Low": 0, "Medium": 0, "High": 0}
    for r in records:
        severity = r.get("severity")
        if severity in counts:
            counts[severity] += 1
    return counts


def build_capa_closure_metric(capa_records: list[dict]) -> dict[str, Any]:
    """CAPA closure rate, effectiveness-check rate, and average time-to-close."""
    total = len(capa_records)
    closed = [r for r in capa_records if str(r.get("status")) == "Closed"]
    closed_with_check = [r for r in closed if as_bool(r.get("effectiveness_check_complete"))]
    close_times = [
        (_to_date(r["closure_date"]) - _to_date(r["opened_date"])).days
        for r in closed
        if r.get("closure_date")
    ]
    return {
        "total_capas": total,
        "closed_count": len(closed),
        "closure_rate": round(len(closed) / total, 4) if total else 0.0,
        "effectiveness_check_rate_at_closure": (
            round(len(closed_with_check) / len(closed), 4) if closed else 0.0
        ),
        "avg_days_to_close": round(sum(close_times) / len(close_times), 1) if close_times else 0.0,
    }


def build_root_cause_breakdown(capa_records: list[dict]) -> dict[str, int]:
    """Count of CAPA records per root_cause category ('Unspecified' if missing)."""
    counts: dict[str, int] = {}
    for r in capa_records:
        root_cause = str(r.get("root_cause") or "").strip() or "Unspecified"
        counts[root_cause] = counts.get(root_cause, 0) + 1
    return counts


def build_quality_metrics(today: date | None = None) -> dict[str, Any]:
    """Assemble the full quality metrics payload for GET /metrics."""
    today = today or date.today()
    deviations = fetch_deviations()
    capas = fetch_capas()

    return {
        "generated_at": today.isoformat(),
        "deviation_aging": build_deviation_aging_metric(deviations, today),
        "capa_aging": build_capa_aging_metric(capas, today),
        "recurrence": build_recurrence_metric(deviations, capas),
        "severity_distribution": {
            "deviations": build_severity_distribution(deviations),
            "capas": build_severity_distribution(capas),
        },
        "capa_closure": build_capa_closure_metric(capas),
        "root_causes": build_root_cause_breakdown(capas),
    }
