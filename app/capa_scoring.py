"""Risk scoring and aging rules for CAPA (Corrective and Preventive Action) records.

Mirrors app/scoring.py's approach for deviations: an explainable, version-
controlled rule set. Every response returns contributing_reasons so reviewers
evaluate — not blindly accept — the prioritization. Aging is computed
alongside the score because a CAPA's time-in-status is itself a quality
signal (stale CAPAs indicate a stalled corrective-action program).

Version history:
  1.0.0 — Initial rule set (severity, due-date, owner, recurrence, root
          cause completeness, effectiveness-check gate, aging tiers)
"""

from datetime import date

from app.scoring import as_bool

# Increment this constant whenever ANY rule weight, threshold, or tier boundary
# changes. Update docs/rule-change-template.md before merging any version bump.
CAPA_SCORING_RULE_VERSION = "1.0.0"

# Aging tiers, in days since opened_date (or opened→closure_date once closed).
# Kept as named constants so docs/risk-rules.md and tests can reference the
# same thresholds instead of re-deriving them.
AGING_TIER_ELEVATED_DAYS = 30
AGING_TIER_CRITICAL_DAYS = 60


def _to_date(value: object) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def compute_aging_days(record: dict[str, object], today: date | None = None) -> int:
    """Days a CAPA has been open, or days it took to close if already closed."""
    today = today or date.today()
    opened = _to_date(record["opened_date"])
    closure_date = record.get("closure_date")
    if str(record.get("status")) == "Closed" and closure_date:
        closure = _to_date(closure_date)
        return max((closure - opened).days, 0)
    return max((today - opened).days, 0)


def score_capa(record: dict[str, object], today: date | None = None) -> dict[str, object]:
    """Score a single CAPA record using the versioned rule set.

    Returns the original record dict enriched with:
        aging_days             int  — days open, or days-to-close if closed
        risk_score             int  — raw point total
        risk_level             str  — High / Medium / Low
        risk_reasons           list — human-readable rule triggers
        scoring_rule_version   str  — rule version that produced this score
    """
    today = today or date.today()
    score = 0
    reasons: list[str] = []

    severity = str(record["severity"])
    status = str(record["status"])
    is_closed = status == "Closed"
    due = _to_date(record["due_date"])
    owner = str(record.get("owner") or "").strip()
    root_cause = str(record.get("root_cause") or "").strip()
    recurrence_flag = as_bool(record["recurrence_flag"])
    effectiveness_check_complete = as_bool(record["effectiveness_check_complete"])
    aging_days = compute_aging_days(record, today)

    if severity == "High":
        score += 3
        reasons.append("High severity")
    elif severity == "Medium":
        score += 1
        reasons.append("Medium severity")

    if not is_closed and due < today:
        score += 3
        reasons.append("Past due date")

    if not owner and not is_closed:
        score += 2
        reasons.append("No CAPA owner assigned")

    if recurrence_flag:
        score += 2
        reasons.append("Recurring root cause")

    if not root_cause:
        score += 1
        reasons.append("Missing root cause")

    if is_closed and not effectiveness_check_complete:
        score += 2
        reasons.append("Closed without a completed effectiveness check")

    if not is_closed:
        if aging_days > AGING_TIER_CRITICAL_DAYS:
            score += 2
            reasons.append(f"Open more than {AGING_TIER_CRITICAL_DAYS} days")
        elif aging_days > AGING_TIER_ELEVATED_DAYS:
            score += 1
            reasons.append(f"Open more than {AGING_TIER_ELEVATED_DAYS} days")

    risk_level = "High" if score >= 5 else "Medium" if score >= 2 else "Low"
    return {
        **record,
        "owner": owner or None,
        "root_cause": root_cause or None,
        "recurrence_flag": recurrence_flag,
        "effectiveness_check_complete": effectiveness_check_complete,
        "aging_days": aging_days,
        "risk_score": score,
        "risk_level": risk_level,
        "risk_reasons": reasons,
        "scoring_rule_version": CAPA_SCORING_RULE_VERSION,
    }
