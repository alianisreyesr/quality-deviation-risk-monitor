"""Quality Deviation Risk Monitor API.

Portfolio-safe FastAPI service: explainable risk scoring, reviewer workflow,
append-only audit trail, and data-quality diagnostics over synthetic data.
"""

from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.audit_db import initialize_audit_table
from app.audit_middleware import AuditMiddleware
from app.audit_router import router as audit_router
from app.cache import get_cached_scored, invalidate_cache
from app.config import CORS_ORIGINS
from app.data_quality_router import router as data_quality_router
from app.database import fetch_deviations, initialize_database
from app.logger import setup_logger
from app.models import DeviationListResponse, DeviationResponse, SummaryResponse
from app.scoring import score_deviation

APP_VERSION = "1.3.0"
logger = setup_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    initialize_audit_table()
    logger.info("Quality Deviation Risk Monitor %s started", APP_VERSION)
    yield


app = FastAPI(
    title="Quality Deviation Risk Monitor",
    description="Portfolio-safe API using synthetic data and transparent risk rules.",
    version=APP_VERSION,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(audit_router)
app.include_router(data_quality_router)


def _load_scored() -> list[dict]:
    return get_cached_scored(lambda: [score_deviation(row) for row in fetch_deviations()])


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
    except Exception as exc:
        logger.warning("Health check warning: %s", exc)
        return {
            "status": "degraded",
            "data_classification": "synthetic portfolio data",
            "decision_support": "human review required",
            "version": APP_VERSION,
            "error": str(exc),
        }


@app.get("/deviations", response_model=DeviationListResponse)
def list_deviations(
    risk_level: str | None = Query(default=None, pattern="^(Low|Medium|High)$"),
):
    records = _load_scored()
    if risk_level:
        records = [r for r in records if r["risk_level"] == risk_level]
    return {"count": len(records), "records": records}


@app.get("/deviations/{deviation_id}", response_model=DeviationResponse)
def get_deviation(deviation_id: str):
    for record in _load_scored():
        if record["deviation_id"] == deviation_id:
            return record
    raise HTTPException(status_code=404, detail="Deviation not found")


@app.get("/summary", response_model=SummaryResponse)
def summary():
    records = _load_scored()
    today = date.today()
    risk_counts = {level: sum(r["risk_level"] == level for r in records) for level in ["Low", "Medium", "High"]}
    review_counts: dict[str, int] = {}
    overdue = 0
    unassigned = 0
    for record in records:
        status = str(record.get("review_status") or "Unknown")
        review_counts[status] = review_counts.get(status, 0) + 1
        due = record["due_date"]
        if isinstance(due, str):
            due = date.fromisoformat(due)
        if due < today:
            overdue += 1
        if not record.get("investigation_owner"):
            unassigned += 1
    return {
        "total_records": len(records),
        "risk_counts": risk_counts,
        "review_status_counts": review_counts,
        "overdue_records": overdue,
        "unassigned_records": unassigned,
    }


@app.post("/cache/invalidate")
def cache_invalidate() -> dict[str, str]:
    invalidate_cache()
    return {"status": "ok", "message": "cache invalidated"}
