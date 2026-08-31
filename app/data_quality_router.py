"""Data quality endpoint.

GET /data-quality
    Returns a per-field quality report for the live synthetic deviation dataset.
    Reports null counts, invalid value counts, and overall issue rate.
    Results are computed on-demand (not cached) to reflect the current state.

This endpoint is diagnostic and portfolio-facing — it is not a validated
quality control system and must not be used for regulated decisions.
"""

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.data_quality import build_capa_data_quality_report, build_data_quality_report
from app.logger import setup_logger
from app.models import DataQualityResponse

logger = setup_logger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Data Quality"])


@router.get(
    "/data-quality",
    response_model=DataQualityResponse,
    summary="Dataset data quality summary",
    description=(
        "Returns null counts, invalid value counts, and issue rates for every "
        "field in the synthetic deviation dataset. Computed on-demand against "
        "the live SQLite database. Intended for portfolio demonstration of "
        "ALCOA+ data integrity awareness — not a validated GxP control."
    ),
)
@limiter.limit("30/minute")
async def data_quality(request: Request) -> DataQualityResponse:
    """Return a per-field data quality report.

    Raises:
        HTTPException 500: Database or analysis error.
    """
    try:
        report = build_data_quality_report()
        logger.info(
            f"Data quality report: {report['total_records']} records, "
            f"{report['records_with_any_issue']} with issues "
            f"({report['issue_rate']:.1%})"
        )
        return DataQualityResponse(**report)
    except Exception as exc:
        logger.error(f"Data quality analysis failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate data quality report")


@router.get(
    "/capas/data-quality",
    response_model=DataQualityResponse,
    summary="CAPA dataset data quality summary",
    description=(
        "Returns unique-ID, null, invalid-value, and issue-rate checks for "
        "every field in the synthetic CAPA dataset — mirrors GET /data-quality "
        "for deviations. Computed on-demand against the live SQLite database."
    ),
)
@limiter.limit("30/minute")
async def capa_data_quality(request: Request) -> DataQualityResponse:
    """Return a per-field data quality report for CAPA records.

    Raises:
        HTTPException 500: Database or analysis error.
    """
    try:
        report = build_capa_data_quality_report()
        logger.info(
            f"CAPA data quality report: {report['total_records']} records, "
            f"{report['records_with_any_issue']} with issues "
            f"({report['issue_rate']:.1%})"
        )
        return DataQualityResponse(**report)
    except Exception as exc:
        logger.error(f"CAPA data quality analysis failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate CAPA data quality report")
