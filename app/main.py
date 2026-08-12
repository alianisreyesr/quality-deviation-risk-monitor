from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.db import fetch_all_deviations, init_db
from app.models import DeviationsListResponse, SummaryResponse, RiskCounts
from app.scoring import score_deviation


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the SQLite database (schema + seed) on startup."""
    init_db()
    yield


app = FastAPI(
    title="Quality Deviation Risk Monitor",
    description=(
        "Portfolio-safe API using synthetic data and transparent, "
        "explainable risk rules. Not for production or regulated use."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _load_scored() -> list[dict]:
    raw = fetch_all_deviations()
    return [score_deviation(record) for record in raw]


@app.get("/health")
def health():
    return {"status": "ok", "data_classification": "synthetic portfolio data", "version": "0.2.0"}


@app.get("/deviations", response_model=DeviationsListResponse)
def deviations(
    risk_level: Optional[str] = Query(
        default=None,
        pattern="^(Low|Medium|High)$",
        description="Filter records by computed risk level.",
    )
):
    records = _load_scored()
    if risk_level:
        records = [r for r in records if r["risk_level"] == risk_level]
    return {"count": len(records), "records": records}


@app.get("/summary", response_model=SummaryResponse)
def summary():
    records = _load_scored()
    risk_counts = {
        level: sum(1 for r in records if r["risk_level"] == level)
        for level in ("Low", "Medium", "High")
    }
    review_counts: dict[str, int] = {}
    for record in records:
        status = record["review_status"]
        review_counts[status] = review_counts.get(status, 0) + 1
    return {
        "total_records": len(records),
        "risk_counts": RiskCounts(**risk_counts),
        "review_status_counts": review_counts,
    }
