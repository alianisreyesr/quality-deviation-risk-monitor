from datetime import date
from pathlib import Path
import csv

from fastapi import FastAPI, Query

app = FastAPI(
    title="Quality Deviation Risk Monitor",
    description="Portfolio-safe API using synthetic data and transparent risk rules.",
    version="0.1.0",
)

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "deviations.csv"


def load_deviations():
    with DATA_FILE.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return [score_deviation(row) for row in rows]


def score_deviation(record):
    score = 0
    reasons = []

    if record["severity"] == "High":
        score += 3
        reasons.append("High severity")
    elif record["severity"] == "Medium":
        score += 1
        reasons.append("Medium severity")

    if date.fromisoformat(record["due_date"]) < date.today():
        score += 3
        reasons.append("Past due date")

    if not record["investigation_owner"].strip():
        score += 2
        reasons.append("No investigation owner assigned")

    if record["repeat_occurrence"].lower() == "true":
        score += 2
        reasons.append("Repeat occurrence")

    if record["record_complete"].lower() != "true":
        score += 2
        reasons.append("Required data is incomplete")

    risk_level = "High" if score >= 5 else "Medium" if score >= 2 else "Low"
    return {**record, "risk_score": score, "risk_level": risk_level, "risk_reasons": reasons}


@app.get("/health")
@limiter.limit("120/minute")
def health(request: Request) -> dict[str, str]:
    try:
        fetch_deviations()
        logger.debug("Health check passed")
        return {
            "status": "ok",
            "data_classification": "synthetic portfolio data",
            "decision_support": "human review required",
            "version": APP_VERSION,
        }
    except Exception as e:
        logger.warning(f"Health check warning: {e}")
        return {
            "status": "degraded",
            "data_classification": "synthetic portfolio data",
            "decision_support": "human review required",
            "version": APP_VERSION,
            "error": str(e),
        }


@app.get("/deviations")
def deviations(risk_level: str | None = Query(default=None, pattern="^(Low|Medium|High)$")):
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
