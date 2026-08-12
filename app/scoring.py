from datetime import date


def as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def score_deviation(record: dict[str, object], today: date | None = None) -> dict[str, object]:
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
    return {**record, "investigation_owner": owner or None, "repeat_occurrence": as_bool(record["repeat_occurrence"]), "record_complete": as_bool(record["record_complete"]), "risk_score": score, "risk_level": risk_level, "risk_reasons": reasons}
