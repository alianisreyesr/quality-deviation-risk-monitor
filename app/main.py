from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query

from app.database import fetch_deviations, initialize_database
from app.models import DeviationListResponse, DeviationResponse, SummaryResponse
from app.scoring import score_deviation


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Quality Deviation Risk Monitor", description="Portfolio-safe API using synthetic data and transparent risk rules.", version="1.0.0", lifespan=lifespan)


def scored_records() -> list[dict[str, object]]:
    return [score_deviation(record) for record in fetch_deviations()]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "data_classification": "synthetic portfolio data", "decision_support": "human review required"}


@app.get("/deviations", response_model=DeviationListResponse)
def deviations(risk_level: str | None = Query(default=None, pattern="^(Low|Medium|High)$"), review_status: str | None = None) -> dict[str, object]:
    records = scored_records()
    if risk_level:
        records = [record for record in records if record["risk_level"] == risk_level]
    if review_status:
        records = [record for record in records if record["review_status"] == review_status]
    return {"count": len(records), "records": records}


@app.get("/deviations/{deviation_id}", response_model=DeviationResponse)
def deviation_detail(deviation_id: str) -> dict[str, object]:
    for record in scored_records():
        if record["deviation_id"] == deviation_id:
            return record
    raise HTTPException(status_code=404, detail="Deviation not found")


@app.get("/summary", response_model=SummaryResponse)
def summary() -> dict[str, object]:
    records = scored_records()
    return {"total_records": len(records), "risk_counts": {level: sum(record["risk_level"] == level for record in records) for level in ["Low", "Medium", "High"]}, "review_status_counts": {status: sum(record["review_status"] == status for record in records) for status in sorted({str(record["review_status"]) for record in records})}, "overdue_records": sum(date.fromisoformat(str(record["due_date"])) < date.today() for record in records), "unassigned_records": sum(not record["investigation_owner"] for record in records)}
