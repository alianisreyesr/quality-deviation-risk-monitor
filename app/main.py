"""Quality Deviation Risk Monitor API.

Portfolio-safe FastAPI service: explainable risk scoring, reviewer workflow,
append-only audit trail, and data-quality diagnostics over synthetic data.
"""

from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.audit_db import initialize_audit_table
from app.audit_middleware import AuditMiddleware
from app.audit_router import router as audit_router
from app.auth import AdminUser
from app.auth_router import router as auth_router
from app.cache import get_cached_scored, invalidate_cache
from app.capa_router import router as capa_router
from app.config import APP_VERSION, CORS_ORIGINS, ENVIRONMENT
from app.data_quality_router import router as data_quality_router
from app.database import fetch_deviations, initialize_database
from app.logger import setup_logger
from app.metrics_router import router as metrics_router
from app.observability import RequestMetricsMiddleware, router as observability_router
from app.models import DeviationListResponse, DeviationResponse, SummaryResponse
from app.rate_limit import ADMIN_LIMIT, READ_LIMIT, limiter
from app.scoring import score_deviation

logger = setup_logger(__name__)


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
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(AuditMiddleware)
app.add_middleware(RequestMetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(data_quality_router)
app.include_router(capa_router)
app.include_router(metrics_router)
app.include_router(observability_router)


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
            "environment": ENVIRONMENT,
        }
    except Exception as exc:
        logger.warning("Health check warning: %s", exc)  # details stay in server logs only
        return {
            "status": "degraded",
            "data_classification": "synthetic portfolio data",
            "decision_support": "human review required",
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
            "error": "database check failed",
        }


@app.get("/deviations", response_model=DeviationListResponse)
@limiter.limit(READ_LIMIT)
def list_deviations(
    request: Request,
    risk_level: str | None = Query(default=None, pattern="^(Low|Medium|High)$"),
):
    records = _load_scored()
    if risk_level:
        records = [r for r in records if r["risk_level"] == risk_level]
    return {"count": len(records), "records": records}


@app.get("/deviations/{deviation_id}", response_model=DeviationResponse)
@limiter.limit(READ_LIMIT)
def get_deviation(request: Request, deviation_id: str):
    for record in _load_scored():
        if record["deviation_id"] == deviation_id:
            return record
    raise HTTPException(status_code=404, detail="Deviation not found")


@app.get("/summary", response_model=SummaryResponse)
@limiter.limit(READ_LIMIT)
def summary(request: Request):
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
@limiter.limit(ADMIN_LIMIT)
def cache_invalidate(request: Request, _admin: AdminUser) -> dict[str, str]:
    invalidate_cache()
    return {"status": "ok", "message": "cache invalidated"}
