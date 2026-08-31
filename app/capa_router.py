"""CAPA (Corrective and Preventive Action) endpoints.

GET /capas
    Scored CAPA records, filterable by risk_level and status.

GET /capas/{capa_id}
    Single CAPA record with explainable risk_reasons[] and aging_days.

POST /capas/{capa_id}/review
    Record a review action (start / submit_for_effectiveness_check / close)
    for a CAPA. Updates capas.status and writes an immutable audit_log
    entry, mirroring POST /deviations/{deviation_id}/review. Closing a CAPA
    is hard-gated on effectiveness_check_complete=true — attempting to close
    without a completed effectiveness check returns HTTP 409, not just a
    risk-score penalty.

GET /capas/{capa_id}/audit-trail
    Return the full audit history for a single CAPA, newest-first.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.audit_db import (
    CapaNotFoundError,
    EffectivenessCheckIncompleteError,
    TransitionNotAllowedError,
    fetch_audit_log,
    fetch_capa_current_status,
    insert_audit_event,
    transition_capa_status,
)
from app.audit_models import (
    CapaAuditEventResponse,
    CapaAuditTrailResponse,
    CapaReviewActionRequest,
    CapaTransitionRejectedResponse,
)
from app.cache import get_cached_scored_capas, invalidate_cache
from app.capa_scoring import score_capa
from app.database import fetch_capas
from app.logger import setup_logger
from app.models import CapaListResponse, CapaResponse

logger = setup_logger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["CAPA"])

# Maps reviewer action → canonical status value stored in the DB.
CAPA_ACTION_TO_STATUS: dict[str, str] = {
    "start": "In Progress",
    "submit_for_effectiveness_check": "Pending Effectiveness Check",
    "close": "Closed",
}

# Allowed transitions: current status → set of actions permitted from that
# state. Closed CAPAs are terminal — re-opening is a separate controlled
# process out of scope here, mirroring ALLOWED_TRANSITIONS in audit_router.py.
CAPA_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Open":                          {"start"},
    "In Progress":                   {"submit_for_effectiveness_check", "close"},
    "Pending Effectiveness Check":   {"close"},
    "Closed":                        set(),
}


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


@router.post(
    "/capas/{capa_id}/review",
    response_model=CapaAuditEventResponse,
    responses={
        404: {"description": "CAPA not found"},
        409: {
            "description": (
                "Transition not permitted from the CAPA's current status, or "
                "the CAPA cannot be closed because its effectiveness check "
                "is incomplete"
            ),
            "model": CapaTransitionRejectedResponse,
        },
    },
    summary="Record a review action on a CAPA",
    description=(
        "Appends an immutable audit event and updates the CAPA's status. "
        "Actor and action are required. Returns HTTP 409 if the requested "
        "action is not permitted from the current status, or if it would "
        "close the CAPA before effectiveness_check_complete is true. "
        "Complies with 21 CFR Part 11 / ALCOA+ traceability requirements."
    ),
)
@limiter.limit("30/minute")
async def review_capa(
    request: Request,
    capa_id: str,
    body: CapaReviewActionRequest,
) -> CapaAuditEventResponse:
    """Record a review action for a CAPA.

    Args:
        capa_id: Target CAPA identifier.
        body: Review action payload (action, actor, optional comment).

    Returns:
        The newly created audit event.

    Raises:
        HTTPException 404: CAPA not found.
        HTTPException 409: Transition not permitted from current status, or
            closing the CAPA before its effectiveness check is complete.
        HTTPException 500: Database error.
    """
    try:
        try:
            previous_status, new_status = transition_capa_status(
                capa_id,
                body.action,
                action_to_status=CAPA_ACTION_TO_STATUS,
                allowed_transitions=CAPA_ALLOWED_TRANSITIONS,
            )
        except CapaNotFoundError:
            logger.warning(f"Review attempted on non-existent CAPA {capa_id}")
            raise HTTPException(status_code=404, detail="CAPA not found")
        except TransitionNotAllowedError as exc:
            logger.warning(
                f"Blocked transition: capa={capa_id} "
                f"status={exc.current_status!r} action={body.action!r} "
                f"allowed={exc.allowed_actions}"
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "detail": f"Action '{body.action}' is not permitted when status is '{exc.current_status}'.",
                    "capa_id": capa_id,
                    "current_status": exc.current_status,
                    "requested_action": body.action,
                    "allowed_actions": exc.allowed_actions,
                },
            )
        except EffectivenessCheckIncompleteError:
            logger.warning(
                f"Blocked close: capa={capa_id} action={body.action!r} "
                "effectiveness_check_complete is false"
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "detail": (
                        "CAPA cannot be closed until its effectiveness check "
                        "is complete (effectiveness_check_complete must be true)."
                    ),
                    "capa_id": capa_id,
                    "requested_action": body.action,
                },
            )

        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")[:512]

        event_id, created_at = insert_audit_event(
            action=body.action,
            actor=body.actor,
            capa_id=capa_id,
            comment=body.comment,
            previous_status=previous_status,
            new_status=new_status,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=200,
        )

        # Invalidate scored cache so the updated status is immediately visible
        invalidate_cache()
        logger.info(
            f"Audit event #{event_id}: capa={capa_id} "
            f"action={body.action} actor={body.actor} "
            f"{previous_status!r} → {new_status!r}"
        )

        return CapaAuditEventResponse(
            event_id=event_id,
            capa_id=capa_id,
            action=body.action,
            actor=body.actor,
            comment=body.comment,
            previous_status=previous_status,
            new_status=new_status,
            created_at=created_at,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to record review action for CAPA {capa_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to record review action")


@router.get(
    "/capas/{capa_id}/audit-trail",
    response_model=CapaAuditTrailResponse,
    responses={404: {"description": "CAPA not found"}},
    summary="Get the audit history for a single CAPA",
    description=(
        "Returns all audit events for a specific CAPA, newest-first, "
        "along with the current status and total event count."
    ),
)
@limiter.limit("60/minute")
async def capa_audit_trail(
    request: Request,
    capa_id: str,
    limit: int = Query(default=100, ge=1, le=500),
) -> CapaAuditTrailResponse:
    """Return the complete audit trail for one CAPA.

    Args:
        capa_id: Target CAPA identifier.
        limit: Maximum number of events to return.

    Returns:
        CapaAuditTrailResponse with current status and event list.

    Raises:
        HTTPException 404: CAPA not found.
        HTTPException 500: Database error.
    """
    try:
        current_status = fetch_capa_current_status(capa_id)
        if current_status is None:
            raise HTTPException(status_code=404, detail="CAPA not found")

        events = fetch_audit_log(capa_id=capa_id, limit=limit)
        logger.info(f"Audit trail fetched: {len(events)} events for CAPA {capa_id}")
        return CapaAuditTrailResponse(
            capa_id=capa_id,
            current_status=current_status,
            event_count=len(events),
            events=events,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to fetch audit trail for CAPA {capa_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail")
