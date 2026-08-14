from typing import Optional
from datetime import date
from pathlib import Path
import csv

from fastapi import FastAPI, Query
from app import config

app = FastAPI(
    title="Quality Deviation Risk Monitor",
    description="Portfolio-safe API using synthetic data and transparent risk rules.",
    version="0.2.0",
)

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "deviations.csv"


def load_deviations():
    with DATA_FILE.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return [score_deviation(row) for row in rows]


def score_deviation(record):
    score = 0
    reasons = []

    # Severity (ICH Q9(R1) §4)
    sev_pts = config.SEVERITY_SCORES.get(record.get("severity", ""), 0)
    if sev_pts:
        score += sev_pts
        reasons.append(f"{record['severity']} severity")

    # Past due date (ICH Q10 §3.2)
    try:
        if date.fromisoformat(record["due_date"]) < date.today():
            score += config.SCORE_PAST_DUE_DATE
            reasons.append("Past due date")
    except (ValueError, KeyError):
        pass

    # No investigation owner (ICH Q10 §3.2)
    if not record.get("investigation_owner", "").strip():
        score += config.SCORE_NO_OWNER
        reasons.append("No investigation owner assigned")

    # Repeat occurrence (ICH Q10 §3.2)
    if record.get("repeat_occurrence", "false").lower() == "true":
        score += config.SCORE_REPEAT_OCCURRENCE
        reasons.append("Repeat occurrence")

    # Record completeness (21 CFR Part 11 / EU Annex 11)
    if record.get("record_complete", "false").lower() != "true":
        score += config.SCORE_INCOMPLETE_RECORD
        reasons.append("Required data is incomplete")

    # Aging (ICH Q10 §3.2 — 30/60-day global closure expectations)
    if record.get("review_status", "").lower() != "closed":
        try:
            age_days = (date.today() - date.fromisoformat(record["opened_date"])).days
            if age_days > config.AGING_THRESHOLD_DAYS_TIER2:
                score += config.AGING_SCORE_TIER1 + config.AGING_SCORE_TIER2
                reasons.append(f"Open more than {config.AGING_THRESHOLD_DAYS_TIER2} days — overdue escalation (ICH Q10)")
            elif age_days > config.AGING_THRESHOLD_DAYS_TIER1:
                score += config.AGING_SCORE_TIER1
                reasons.append(f"Open more than {config.AGING_THRESHOLD_DAYS_TIER1} days (ICH Q10)")
        except (ValueError, KeyError):
            pass

    risk_level = (
        "High"   if score >= config.RISK_THRESHOLD_HIGH   else
        "Medium" if score >= config.RISK_THRESHOLD_MEDIUM else
        "Low"
    )
    return {**record, "risk_score": score, "risk_level": risk_level, "risk_reasons": reasons}


@app.get("/health")
def health():
    return {"status": "ok", "data_classification": "synthetic portfolio data"}


@app.get("/deviations")
def deviations(risk_level: Optional[str] = Query(default=None, pattern="^(Low|Medium|High)$")):
    records = load_deviations()
    if risk_level:
        records = [r for r in records if r["risk_level"] == risk_level]
    return {"count": len(records), "records": records}


@app.get("/summary")
def summary():
    records = load_deviations()
    risk_counts = {level: sum(r["risk_level"] == level for r in records) for level in ["Low", "Medium", "High"]}
    review_counts = {}
    for r in records:
        status = r["review_status"]
        review_counts[status] = review_counts.get(status, 0) + 1
    return {"total_records": len(records), "risk_counts": risk_counts, "review_status_counts": review_counts}
