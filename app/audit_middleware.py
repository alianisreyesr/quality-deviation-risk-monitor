"""Audit middleware — generic safety-net logger for mutating HTTP requests.

POST /deviations/{id}/review is intentionally NOT logged here: audit_router
writes it directly with domain detail (previous_status/new_status, atomic
transition validation) that this generic middleware can't reconstruct from
the request alone. This middleware instead exists so any *other* mutating
endpoint — present (POST /cache/invalidate) or added later without its own
explicit insert_audit_event call — still leaves a trace rather than
silently going unaudited.

Complies with 21 CFR Part 11 / ALCOA+ requirements:
- Immutable, append-only log (no UPDATE/DELETE on audit_log)
- UTC timestamps on every record
- Actor identity taken from the verified bearer token (never from the body
  or a client-supplied header)
- IP address and User-Agent captured for traceability
"""

import json
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.audit_db import insert_audit_event
from app.auth import decode_token
from app.logger import setup_logger

logger = setup_logger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# Paths that are NOT subject to audit logging (infrastructure, not data)
# /auth/token is excluded so credentials in the request body can never be
# persisted into the audit log.
EXCLUDED_PATHS = {"/docs", "/openapi.json", "/redoc", "/auth/token"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that records mutating requests not already
    logged with richer detail by their own route handler.

    Captures:
    - path, method, HTTP status code
    - actor (verified bearer-token subject; "anonymous" if no valid token)
    - request body snapshot (truncated to 2 000 chars)
    - client IP address and User-Agent
    - response latency (milliseconds)
    - UTC timestamp
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if request.method not in MUTATING_METHODS:
            return await call_next(request)
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        start = datetime.now(timezone.utc)

        # Read and buffer request body so downstream handlers can also read it
        raw_body = await request.body()
        body_snapshot: str | None = None

        if raw_body:
            try:
                body_snapshot = json.dumps(json.loads(raw_body))[:2000]
            except (json.JSONDecodeError, ValueError):
                body_snapshot = raw_body.decode(errors="replace")[:2000]

        # The actor comes only from a verified token. Body 'actor' fields and
        # the legacy X-Actor header are self-asserted and therefore ignored.
        actor = _authenticated_actor(request)

        response = await call_next(request)

        elapsed_ms = round(
            (datetime.now(timezone.utc) - start).total_seconds() * 1000, 2
        )

        # Domain review events are written by audit_router. Skip 4xx/5xx so a
        # rejected transition does not pollute the append-only trail.
        if response.status_code >= 400:
            return response
        if request.url.path.rstrip("/").endswith("/review"):
            return response

        ip_address = (
            request.client.host if request.client else "unknown"
        )
        user_agent = request.headers.get("User-Agent", "")[:512]

        try:
            insert_audit_event(
                action=f"{request.method} {request.url.path}",
                actor=actor,
                comment=body_snapshot,
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=response.status_code,
                latency_ms=elapsed_ms,
                deviation_id=_extract_deviation_id(request.url.path),
            )
        except Exception as exc:
            # Audit failure must NEVER break the response — log and continue
            logger.error(f"Audit middleware failed to log event: {exc}")

        return response


def _authenticated_actor(request: Request) -> str:
    """Return the verified token subject, or "anonymous" without a valid token."""
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() == "bearer" and token:
        user = decode_token(token.strip())
        if user is not None:
            return user.username[:100]
    return "anonymous"


def _extract_deviation_id(path: str) -> str | None:
    """Extract deviation_id from paths like /deviations/{id}/review."""
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "deviations":
        return parts[1]
    return None
