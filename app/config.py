"""Application configuration.

All environment-tunable settings live here. Import constants from
this module rather than hardcoding values in other modules.
"""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "data" / "deviations.csv"
CAPA_DATA_FILE = ROOT_DIR / "data" / "capas.csv"
DATABASE_FILE = ROOT_DIR / "data" / "quality_monitor.db"
SCHEMA_FILE = ROOT_DIR / "sql" / "schema.sql"
TRANSFORMATIONS_FILE = ROOT_DIR / "sql" / "transformations.sql"

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Comma-separated list of allowed origins.  Override via environment variable
# for staging / production deployments; defaults to local Vite dev server.
#
# Example (shell):
#   export CORS_ORIGINS="https://my-app.example.com,https://staging.example.com"
# ---------------------------------------------------------------------------
_raw = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
CORS_ORIGINS: list[str] = [o.strip() for o in _raw.split(",") if o.strip()]

# ---------------------------------------------------------------------------
# Runtime identity
# ---------------------------------------------------------------------------
APP_VERSION = "1.5.0"

# "development" (default), "test", or a production-like value
# ("production", "prod", "staging"). Production-like values make the API
# refuse to start without a strong JWT_SECRET_KEY (see app/auth.py).
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip().lower()
PRODUCTION_ENVIRONMENTS = {"production", "prod", "staging"}

# ---------------------------------------------------------------------------
# Authentication (JWT)
# ---------------------------------------------------------------------------
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))
JWT_MIN_SECRET_LENGTH = 32
