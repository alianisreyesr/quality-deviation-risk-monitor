"""Quality metrics endpoint.

GET /metrics
    Aggregated metrics across deviations and CAPA: aging, recurrence,
    severity distribution, CAPA closure rate, and root-cause breakdown.
    Computed on-demand (not cached) so the numbers always reflect the
    current dataset — see app/metrics.py for the calculations.

Diagnostic and portfolio-facing, like GET /data-quality — not a validated
GxP KPI system.
"""

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.logger import setup_logger
from app.metrics import build_quality_metrics
from app.models import QualityMetricsResponse

logger = setup_logger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    response_model=QualityMetricsResponse,
    summary="Aggregated quality metrics",
    description=(
        "Aging, recurrence, severity distribution, CAPA closure rate, and "
        "root-cause breakdown, computed live from deviations and CAPA "
        "records. Intended to back an initial BI dashboard (see "
        "docs/dashboard.md)."
    ),
)
@limiter.limit("30/minute")
def metrics(request: Request) -> QualityMetricsResponse:
    try:
        payload = build_quality_metrics()
        logger.info(
            "Quality metrics computed: %d deviations open, %d CAPAs open",
            payload["deviation_aging"]["open_count"],
            payload["capa_aging"]["open_count"],
        )
        return QualityMetricsResponse(**payload)
    except Exception as exc:
        logger.error(f"Quality metrics computation failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to compute quality metrics")
