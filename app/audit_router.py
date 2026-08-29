"""Audit trail endpoints.

POST /deviations/{deviation_id}/review
    Record a review action (acknowledge / investigate / close) for a deviation.
    Updates deviation.review_status and writes an immutable audit_log entry.
    Complies with 21 CFR Part 11: actor required, timestamp server-generated,
    previous + new status both recorded.
    Returns HTTP 409 if the requested transition is not permitted from the
    deviation's current status.

GET /deviations/{deviation_id}/audit-trail
    Return the full audit history for a single deviation, newest-first.
    Includes current review_status and event count.

GET /audit-log
    Return the full immutable audit log, newest first.
    Optional ?deviation_id= query param to filter by deviation.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.audit_db import (
    DeviationNotFoundError,
    TransitionNotAllowedError,
    fetch_audit_log,
    fetch_deviation_current_status,
    insert_audit_event,
    transition_deviation_status,
)
from app.audit_models import (
    AuditEventResponse,
    AuditTrailResponse,
    ReviewActionRequest,
    TransitionRejectedResponse,
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

# Allowed transitions: current_status → set of actions permitted from that state.
# Deviations that are Closed cannot be acted upon — they must be re-opened via
# a separate controlled process (out of scope for this prototype).
# A deviation already Under Review cannot be re-acknowledged (no-op prevention).
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Open":                      {"acknowledge", "investigate"},
    "Under Review":              {"investigate", "close"},
    "Investigation In Progress": {"close"},
    "Closed":                    set(),  # terminal state — no further actions
}


@router.post(
    "/deviations/{deviation_id}/review",
    response_model=AuditEventResponse,
    responses={
        404: {"description": "Deviation not found"},
        409: {
            "description": "Transition not permitted from the deviation's current status",
            "model": TransitionRejectedResponse,
        },
    },
    summary="Record a review action on a deviation",
    description=(
        "Appends an immutable audit event and updates the deviation's "
        "review_status. Actor and action are required. Returns HTTP 409 if the "
        "requested action is not permitted from the current status. "
        "Complies with 21 CFR Part 11 / ALCOA+ traceability requirements."
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
        HTTPException 409: Transition not permitted from current status.
        HTTPException 500: Database error.
    """
    try:
        # --- Validate and apply the transition atomically ---
        # transition_deviation_status takes SQLite's write lock before it
        # reads the current status, so two concurrent requests for the same
        # deviation can't both observe the same pre-transition status and
        # both succeed (see its docstring for the race this closes).
        try:
            previous_status, new_status = transition_deviation_status(
                deviation_id,
                body.action,
                action_to_status=ACTION_TO_STATUS,
                allowed_transitions=ALLOWED_TRANSITIONS,
            )
        except DeviationNotFoundError:
            logger.warning(f"Review attempted on non-existent deviation {deviation_id}")
            raise HTTPException(status_code=404, detail="Deviation not found")
        except TransitionNotAllowedError as exc:
            logger.warning(
                f"Blocked transition: deviation={deviation_id} "
                f"status={exc.current_status!r} action={body.action!r} "
                f"allowed={exc.allowed_actions}"
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "detail": f"Action '{body.action}' is not permitted when status is '{exc.current_status}'.",
                    "deviation_id": deviation_id,
                    "current_status": exc.current_status,
                    "requested_action": body.action,
                    "allowed_actions": exc.allowed_actions,
                },
            )

        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")[:512]

        event_id, created_at = insert_audit_event(
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
            created_at=created_at,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to record review action for {deviation_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to record review action")


@router.get(
    "/deviations/{deviation_id}/audit-trail",
    response_model=AuditTrailResponse,
    responses={404: {"description": "Deviation not found"}},
    summary="Get the audit history for a single deviation",
    description=(
        "Returns all audit events for a specific deviation, newest-first, "
        "along with the current review_status and total event count. "
        "Useful for reviewers verifying the full traceability chain of a record."
    ),
)
@limiter.limit("60/minute")
async def deviation_audit_trail(
    request: Request,
    deviation_id: str,
    limit: int = Query(default=100, ge=1, le=500),
) -> AuditTrailResponse:
    """Return the complete audit trail for one deviation.

    Args:
        deviation_id: Target deviation identifier.
        limit: Maximum number of events to return.

    Returns:
        AuditTrailResponse with current status and event list.

    Raises:
        HTTPException 404: Deviation not found.
        HTTPException 500: Database error.
    """
    try:
        current_status = fetch_deviation_current_status(deviation_id)
        if current_status is None:
            raise HTTPException(status_code=404, detail="Deviation not found")

        events = fetch_audit_log(deviation_id=deviation_id, limit=limit)
        logger.info(
            f"Audit trail fetched: {len(events)} events for deviation {deviation_id}"
        )
        return AuditTrailResponse(
            deviation_id=deviation_id,
            current_review_status=current_status,
            event_count=len(events),
            events=events,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to fetch audit trail for {deviation_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail")


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
