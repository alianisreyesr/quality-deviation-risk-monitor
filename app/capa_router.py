"""CAPA (Corrective and Preventive Action) endpoints.

GET /capas
    Scored CAPA records, filterable by risk_level and status.

GET /capas/{capa_id}
    Single CAPA record with explainable risk_reasons[] and aging_days.

Read-only by design for this portfolio prototype — CAPA review/closure
workflow (with an audit trail, mirroring app/audit_router.py for deviations)
is a natural next step but out of scope here.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.cache import get_cached_scored_capas
from app.capa_scoring import score_capa
from app.database import fetch_capas
from app.logger import setup_logger
from app.models import CapaListResponse, CapaResponse

logger = setup_logger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["CAPA"])


def _load_scored_capas() -> list[dict]:
    return get_cached_scored_capas(lambda: [score_capa(row) for row in fetch_capas()])


@router.get(
    "/capas",
    response_model=CapaListResponse,
    summary="List scored CAPA records",
    description=(
        "Returns every CAPA record enriched with an explainable risk score, "
        "risk_level, risk_reasons[], and aging_days. Filterable by risk_level "
        "and status."
    ),
)
@limiter.limit("100/minute")
def list_capas(
    request: Request,
    risk_level: str | None = Query(default=None, pattern="^(Low|Medium|High)$"),
    status: str | None = Query(
        default=None,
        pattern="^(Open|In Progress|Pending Effectiveness Check|Closed)$",
    ),
) -> CapaListResponse:
    records = _load_scored_capas()
    if risk_level:
        records = [r for r in records if r["risk_level"] == risk_level]
    if status:
        records = [r for r in records if r["status"] == status]
    return {"count": len(records), "records": records}


@router.get(
    "/capas/{capa_id}",
    response_model=CapaResponse,
    responses={404: {"description": "CAPA not found"}},
    summary="Get a single scored CAPA record",
)
@limiter.limit("100/minute")
def get_capa(request: Request, capa_id: str) -> CapaResponse:
    for record in _load_scored_capas():
        if record["capa_id"] == capa_id:
            return record
    raise HTTPException(status_code=404, detail="CAPA not found")
