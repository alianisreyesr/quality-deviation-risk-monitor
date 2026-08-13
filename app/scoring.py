"""Risk scoring rules for deviation records.

All rule weights and thresholds are versioned under SCORING_RULE_VERSION.
Include this version in every score response so results can be traced back
to the exact rule set that produced them — consistent with 21 CFR Part 11
and ALCOA+ traceability requirements.

Version history:
  1.0.0 — Initial rule set (severity, due-date, owner, recurrence, completeness)
"""

from datetime import date

# Increment this constant whenever ANY rule weight, threshold, or tier boundary changes.
# Update docs/rule-change-template.md before merging any version bump.
SCORING_RULE_VERSION = "1.0.0"


def as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def score_deviation(record: dict[str, object], today: date | None = None) -> dict[str, object]:
    """Score a single deviation record using the versioned rule set.

    Returns the original record dict enriched with:
        risk_score            int  — raw point total
        risk_level            str  — High / Medium / Low
        risk_reasons          list — human-readable rule triggers
        scoring_rule_version  str  — rule version that produced this score
    """
    today = today or date.today()
    score = 0
    reasons: list[str] = []
    severity = str(record["severity"])
    due_date = record["due_date"]
    due = due_date if isinstance(due_date, date) else date.fromisoformat(str(due_date))
    owner = str(record.get("investigation_owner") or "").strip()

    if severity == "High":
        score += 3
        reasons.append("High severity")
    elif severity == "Medium":
        score += 1
        reasons.append("Medium severity")
    if due < today:
        score += 3
        reasons.append("Past due date")
    if not owner:
        score += 2
        reasons.append("No investigation owner assigned")
    if as_bool(record["repeat_occurrence"]):
        score += 2
        reasons.append("Repeat occurrence")
    if not as_bool(record["record_complete"]):
        score += 2
        reasons.append("Required data is incomplete")

    risk_level = "High" if score >= 5 else "Medium" if score >= 2 else "Low"
    return {
        **record,
        "investigation_owner": owner or None,
        "repeat_occurrence": as_bool(record["repeat_occurrence"]),
        "record_complete": as_bool(record["record_complete"]),
        "risk_score": score,
        "risk_level": risk_level,
        "risk_reasons": reasons,
        "scoring_rule_version": SCORING_RULE_VERSION,
    }
