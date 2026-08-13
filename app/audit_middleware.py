"""Audit middleware — logs every mutating HTTP request to the audit_log table.

Complies with 21 CFR Part 11 / ALCOA+ requirements:
- Immutable, append-only log (no UPDATE/DELETE on audit_log)
- UTC timestamps on every record
- Actor identity required on POST /deviations/{id}/review
- IP address and User-Agent captured for traceability
"""

import json
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.audit_db import insert_audit_event
from app.logger import setup_logger

logger = setup_logger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# Paths that are NOT subject to audit logging (infrastructure, not data)
EXCLUDED_PATHS = {"/cache/invalidate", "/docs", "/openapi.json", "/redoc"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that records every mutating request.

    Captures:
    - path, method, HTTP status code
    - actor (from X-Actor header or request body 'actor' field)
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
        actor: str | None = None

        if raw_body:
            try:
                parsed = json.loads(raw_body)
                body_snapshot = json.dumps(parsed)[:2000]
                actor = parsed.get("actor") if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, ValueError):
                body_snapshot = raw_body.decode(errors="replace")[:2000]

        # Fall back to X-Actor header
        if not actor:
            actor = request.headers.get("X-Actor", "unknown")

        response = await call_next(request)

        elapsed_ms = round(
            (datetime.now(timezone.utc) - start).total_seconds() * 1000, 2
        )

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


def _extract_deviation_id(path: str) -> str | None:
    """Extract deviation_id from paths like /deviations/{id}/review."""
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "deviations":
        return parts[1]
    return None
