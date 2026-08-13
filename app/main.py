from datetime import date

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import CORS_ORIGINS
from app.database import fetch_deviations, initialize_database
from app.audit_db import initialize_audit_table
from app.audit_middleware import AuditMiddleware
from app.audit_router import router as audit_router
from app.data_quality_router import router as data_quality_router
from app.models import DeviationListResponse, DeviationResponse, SummaryResponse
from app.scoring import score_deviation
from app.cache import get_cached_scored, invalidate_cache
from app.logger import setup_logger

APP_VERSION = "1.3.0"

logger = setup_logger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        logger.info("Starting application initialization...")
        initialize_database()
        initialize_audit_table()
        logger.info("Application successfully initialized")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title="Quality Deviation Risk Monitor",
    description="Portfolio-safe API using synthetic data and transparent risk rules.",
    version=APP_VERSION,
    lifespan=lifespan,
)
app.state.limiter = limiter

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)

# --- Routers ---
app.include_router(audit_router)
app.include_router(data_quality_router)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded: 100 requests per minute per IP",
            "retry_after": 60,
        },
    )


def scored_records() -> list[dict[str, object]]:
    try:
        return get_cached_scored(lambda: [
            score_deviation(record)
            for record in fetch_deviations()
        ])
    except Exception as e:
        logger.error(f"Failed to load scored deviations: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load deviation records",
        )


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
        records = [record for record in records if record["risk_level"] == risk_level]
    return {"count": len(records), "records": records}


@app.get("/summary")
def summary():
    records = load_deviations()
    risk_counts = {level: sum(record["risk_level"] == level for record in records) for level in ["Low", "Medium", "High"]}
    review_counts = {}
    for record in records:
        status = record["review_status"]
        review_counts[status] = review_counts.get(status, 0) + 1
    return {"total_records": len(records), "risk_counts": risk_counts, "review_status_counts": review_counts}
