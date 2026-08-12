from datetime import date
from typing import Any


SEVERITY_SCORES: dict[str, int] = {"High": 3, "Medium": 1, "Low": 0}


def score_deviation(record: dict[str, Any]) -> dict[str, Any]:
    """Apply transparent, explainable risk rules to a single deviation record.

    Rules (additive):
        +3  High severity
        +1  Medium severity
        +3  Due date is in the past
        +2  No investigation owner assigned
        +2  Repeat occurrence
        +2  Record is incomplete

    Thresholds:
        score >= 5 -> High
        score >= 2 -> Medium
        else       -> Low
    """
    score = 0
    reasons: list[str] = []

    severity = record.get("severity", "")
    severity_score = SEVERITY_SCORES.get(severity, 0)
    if severity_score > 0:
        score += severity_score
        reasons.append(f"{severity} severity")

    try:
        due = date.fromisoformat(str(record["due_date"]))
        if due < date.today():
            score += 3
            reasons.append("Past due date")
    except (ValueError, KeyError):
        pass

    owner = record.get("investigation_owner") or ""
    if not str(owner).strip():
        score += 2
        reasons.append("No investigation owner assigned")

    repeat = record.get("repeat_occurrence")
    if repeat in (True, 1, "True", "true", "1"):
        score += 2
        reasons.append("Repeat occurrence")

    complete = record.get("record_complete")
    if complete not in (True, 1, "True", "true", "1"):
        score += 2
        reasons.append("Required data is incomplete")

    risk_level = "High" if score >= 5 else "Medium" if score >= 2 else "Low"
    return {**record, "risk_score": score, "risk_level": risk_level, "risk_reasons": reasons}
