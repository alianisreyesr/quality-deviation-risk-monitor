from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import fetch_deviations, initialize_database
from app.audit_db import initialize_audit_table
from app.audit_middleware import AuditMiddleware
from app.audit_router import router as audit_router
from app.models import DeviationListResponse, DeviationResponse, SummaryResponse
from app.scoring import score_deviation
from app.cache import get_cached_scored, invalidate_cache
from app.logger import setup_logger

logger = setup_logger(__name__)

# Rate limiter: 100 requests per minute per IP
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
    version="1.1.0",
    lifespan=lifespan,
)
app.state.limiter = limiter

# --- Middleware (order matters: CORS first, then Audit) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)

# --- Routers ---
app.include_router(audit_router)

# --- Rate limit error handler ---
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
    """Load and score deviations with caching.

    Returns:
        List of scored deviation records

    Raises:
        HTTPException: If data loading fails
    """
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
    """Health check endpoint."""
    try:
        fetch_deviations()
        logger.debug("Health check passed")
        return {
            "status": "ok",
            "data_classification": "synthetic portfolio data",
            "decision_support": "human review required",
            "version": "1.1.0",
        }
    except Exception as e:
        logger.warning(f"Health check warning: {e}")
        return {
            "status": "degraded",
            "data_classification": "synthetic portfolio data",
            "decision_support": "human review required",
            "version": "1.1.0",
            "error": str(e),
        }


@app.get("/deviations", response_model=DeviationListResponse)
@limiter.limit("100/minute")
def deviations(
    request: Request,
    risk_level: str | None = Query(default=None, pattern="^(Low|Medium|High)$"),
    review_status: str | None = None,
) -> dict[str, object]:
    """Get all deviations with optional filtering.

    Args:
        risk_level: Optional filter for Low, Medium, or High risk
        review_status: Optional filter for review status

    Returns:
        List of deviations with risk scores

    Raises:
        HTTPException: If data loading fails
    """
    try:
        records = scored_records()

        if risk_level:
            original_count = len(records)
            records = [r for r in records if r["risk_level"] == risk_level]
            logger.info(f"Filtered {len(records)} records at {risk_level} risk level (from {original_count} total)")

        if review_status:
            records = [r for r in records if r["review_status"] == review_status]

        logger.info(f"Retrieved {len(records)} deviations")
        return {"count": len(records), "records": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving deviations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve deviations")


@app.get("/deviations/{deviation_id}", response_model=DeviationResponse)
@limiter.limit("100/minute")
def deviation_detail(request: Request, deviation_id: str) -> dict[str, object]:
    """Get details for a specific deviation.

    Args:
        deviation_id: The deviation ID to retrieve

    Returns:
        Deviation record with risk score

    Raises:
        HTTPException: If deviation not found or data loading fails
    """
    try:
        for record in scored_records():
            if record["deviation_id"] == deviation_id:
                logger.info(f"Retrieved deviation {deviation_id}")
                return record
        logger.warning(f"Deviation {deviation_id} not found")
        raise HTTPException(status_code=404, detail="Deviation not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving deviation {deviation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve deviation")


@app.get("/summary", response_model=SummaryResponse)
@limiter.limit("100/minute")
def summary(request: Request) -> dict[str, object]:
    """Get summary statistics of deviations.

    Returns:
        Summary with counts by risk level and review status

    Raises:
        HTTPException: If data loading fails
    """
    try:
        records = scored_records()

        risk_counts = {
            level: sum(r["risk_level"] == level for r in records)
            for level in ["Low", "Medium", "High"]
        }

        review_status_counts = {
            status: sum(r["review_status"] == status for r in records)
            for status in sorted({str(r["review_status"]) for r in records})
        }

        overdue = sum(date.fromisoformat(str(r["due_date"])) < date.today() for r in records)
        unassigned = sum(not r["investigation_owner"] for r in records)

        logger.info(
            f"Summary: {len(records)} total, Risk={risk_counts}, "
            f"Review statuses={list(review_status_counts.keys())}, "
            f"Overdue={overdue}, Unassigned={unassigned}"
        )

        return {
            "total_records": len(records),
            "risk_counts": risk_counts,
            "review_status_counts": review_status_counts,
            "overdue_records": overdue,
            "unassigned_records": unassigned,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@app.post("/cache/invalidate")
@limiter.limit("10/minute")
def cache_invalidate(request: Request) -> dict[str, str]:
    """Manually invalidate the scored deviations cache.

    Useful for refreshing data without restarting the server.
    """
    try:
        invalidate_cache()
        logger.info("Cache invalidated via API endpoint")
        return {"status": "cache invalidated"}
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")
