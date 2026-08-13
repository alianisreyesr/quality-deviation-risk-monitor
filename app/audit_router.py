"""Audit trail endpoints.

POST /deviations/{deviation_id}/review
    Record a review action (acknowledge / investigate / close) for a deviation.
    Updates deviation.review_status and writes an immutable audit_log entry.
    Complies with 21 CFR Part 11: actor required, timestamp server-generated,
    previous + new status both recorded.

GET /audit-log
    Return the full immutable audit log, newest first.
    Optional ?deviation_id= query param to filter by deviation.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.audit_models import AuditEventResponse, ReviewActionRequest
from app.audit_db import (
    fetch_audit_log,
    insert_audit_event,
    update_deviation_status,
)
from app.cache import invalidate_cache
from app.logger import setup_logger

logger = setup_logger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Audit Trail"])

# Maps reviewer action → canonical review_status value stored in the DB
ACTION_TO_STATUS: dict[str, str] = {
    "acknowledge": "Under Review",
    "investigate": "Investigation In Progress",
    "close": "Closed",
}


@router.post(
    "/deviations/{deviation_id}/review",
    response_model=AuditEventResponse,
    summary="Record a review action on a deviation",
    description=(
        "Appends an immutable audit event and updates the deviation's "
        "review_status. Actor and action are required. Complies with "
        "21 CFR Part 11 / ALCOA+ traceability requirements."
    ),
)
@limiter.limit("30/minute")
async def review_deviation(
    request: Request,
    deviation_id: str,
    body: ReviewActionRequest,
) -> AuditEventResponse:
    """Record a review action for a deviation.

    Args:
        deviation_id: Target deviation identifier.
        body: Review action payload (action, actor, optional comment).

    Returns:
        The newly created audit event.

    Raises:
        HTTPException 404: Deviation not found.
        HTTPException 500: Database error.
    """
    try:
        new_status = ACTION_TO_STATUS[body.action]
        previous_status = update_deviation_status(deviation_id, new_status)

        if previous_status is None:
            logger.warning(f"Review attempted on non-existent deviation {deviation_id}")
            raise HTTPException(status_code=404, detail="Deviation not found")

        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")[:512]

        event_id = insert_audit_event(
            action=body.action,
            actor=body.actor,
            deviation_id=deviation_id,
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
            f"Audit event #{event_id}: deviation={deviation_id} "
            f"action={body.action} actor={body.actor} "
            f"{previous_status!r} → {new_status!r}"
        )

        return AuditEventResponse(
            event_id=event_id,
            deviation_id=deviation_id,
            action=body.action,
            actor=body.actor,
            comment=body.comment,
            previous_status=previous_status,
            new_status=new_status,
            created_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to record review action for {deviation_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to record review action")


@router.get(
    "/audit-log",
    summary="Retrieve the immutable audit log",
    description=(
        "Returns audit events newest-first. Use ?deviation_id= to filter "
        "by deviation. Max 500 rows per request."
    ),
)
@limiter.limit("60/minute")
async def get_audit_log(
    request: Request,
    deviation_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, object]:
    """Return the audit log, optionally filtered by deviation_id."""
    try:
        events = fetch_audit_log(deviation_id=deviation_id, limit=limit)
        logger.info(
            f"Audit log fetched: {len(events)} events"
            + (f" for deviation {deviation_id}" if deviation_id else "")
        )
        return {"count": len(events), "events": events}
    except Exception as exc:
        logger.error(f"Failed to fetch audit log: {exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit log")
