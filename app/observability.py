"""Dependency-free HTTP telemetry in Prometheus exposition format."""

from __future__ import annotations

import threading
import time
from collections import defaultdict

from fastapi import APIRouter, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self.duration_seconds: dict[tuple[str, str], float] = defaultdict(float)

    def observe(self, method: str, route: str, status: int, duration: float) -> None:
        with self._lock:
            self.requests[(method, route, status)] += 1
            self.duration_seconds[(method, route)] += duration

    def render(self) -> str:
        lines = [
            "# HELP http_requests_total Total HTTP requests.",
            "# TYPE http_requests_total counter",
        ]
        with self._lock:
            for (method, route, status), count in sorted(self.requests.items()):
                lines.append(f'http_requests_total{{method="{method}",route="{route}",status="{status}"}} {count}')
            lines.extend([
                "# HELP http_request_duration_seconds_sum Cumulative HTTP request duration.",
                "# TYPE http_request_duration_seconds_sum counter",
            ])
            for (method, route), duration in sorted(self.duration_seconds.items()):
                lines.append(f'http_request_duration_seconds_sum{{method="{method}",route="{route}"}} {duration:.6f}')
        return "\n".join(lines) + "\n"


REQUEST_METRICS = RequestMetrics()


class RequestMetricsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()
        status = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            route = scope.get("route")
            route_path = getattr(route, "path", scope.get("path", "unknown"))
            if route_path != "/internal/metrics":
                REQUEST_METRICS.observe(scope["method"], route_path, status, time.perf_counter() - started)


router = APIRouter(tags=["Operations"])


@router.get("/internal/metrics", include_in_schema=False)
def prometheus_metrics() -> Response:
    return Response(REQUEST_METRICS.render(), media_type="text/plain; version=0.0.4")
