"""Single shared rate limiter.

One ``Limiter`` instance is used by every router so that all limits share the
same storage and the exception handler registered on ``app.state.limiter``
applies uniformly. Limits are per client IP (``slowapi``, in-memory storage,
process-local).
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# RATE_LIMIT_ENABLED=false disables limiting (used by the test suite only).
limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() != "false",
)

# Documented limits (see IMPROVEMENTS.md and README).
READ_LIMIT = "100/minute"      # /deviations, /deviations/{id}, /summary, /capas*
DIAGNOSTIC_LIMIT = "30/minute"  # /data-quality, /metrics
WRITE_LIMIT = "30/minute"      # review actions
LOGIN_LIMIT = "10/minute"      # POST /auth/token
ADMIN_LIMIT = "10/minute"      # POST /cache/invalidate
