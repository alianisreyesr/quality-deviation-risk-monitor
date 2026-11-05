"""JWT authentication and role authorization.

The audit-trail ``actor`` is taken from the verified token subject, never from the
request body or a client-supplied header. Demo accounts are synthetic: only
PBKDF2 hashes are stored; there is no user store or identity provider.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import warnings
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app import config


class Role(str, Enum):
    reviewer = "reviewer"
    quality_manager = "quality_manager"
    admin = "admin"


class User(BaseModel):
    username: str
    role: Role


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


_PBKDF2_ITERATIONS = 200_000

# Synthetic demo accounts: (role, salt hex, PBKDF2-HMAC-SHA256 hex digest).
_USERS: dict[str, tuple[Role, str, str]] = {
    "reviewer.demo": (Role.reviewer, "7164726d2d72657669657765722e64656d6f", "4ed326d5ab7fe8aa06057a493c17d463f7ab367598303dc462b18cea2a2d3f02"),
    "quality.demo": (Role.quality_manager, "7164726d2d7175616c6974792e64656d6f", "b0ba625c32f30c9c38eabe8ec3419a4fbc098573b4f12889e94720b428af6ca0"),
    "admin.demo": (Role.admin, "7164726d2d61646d696e2e64656d6f", "642530eb136144d9fc6365621f69e6bf692240c08d552f438cab50817fbdcecc"),
}

# Roles permitted per workflow action (admin is always permitted).
# Closing a record is reserved for quality management (segregation of duties).
DEVIATION_ACTION_ROLES: dict[str, set[Role]] = {
    "acknowledge": {Role.reviewer, Role.quality_manager},
    "investigate": {Role.reviewer, Role.quality_manager},
    "close": {Role.quality_manager},
}
CAPA_ACTION_ROLES: dict[str, set[Role]] = {
    "start": {Role.reviewer, Role.quality_manager},
    "submit_for_effectiveness_check": {Role.reviewer, Role.quality_manager},
    "close": {Role.quality_manager},
}


def _load_secret() -> str:
    """Return the JWT signing key from JWT_SECRET_KEY.

    Production-like environments must provide a strong, stable secret; startup
    fails otherwise. In development an ephemeral random secret is generated (tokens
    reset on restart and do not work across workers).
    """
    configured = os.environ.get("JWT_SECRET_KEY")
    if config.ENVIRONMENT in config.PRODUCTION_ENVIRONMENTS:
        if not configured or len(configured) < config.JWT_MIN_SECRET_LENGTH:
            raise RuntimeError(
                f"JWT_SECRET_KEY must be set to at least {config.JWT_MIN_SECRET_LENGTH} "
                f"characters when ENVIRONMENT={config.ENVIRONMENT}"
            )
        return configured
    if configured:
        return configured
    warnings.warn(
        "JWT_SECRET_KEY is not set; using an ephemeral secret (tokens reset on restart). "
        "Set JWT_SECRET_KEY for any shared or production deployment.",
        stacklevel=2,
    )
    return secrets.token_urlsafe(48)


_SECRET = _load_secret()
ACCESS_TOKEN_TTL_SECONDS = config.JWT_EXPIRES_MINUTES * 60
_bearer = HTTPBearer(auto_error=False)


def authenticate(username: str, password: str) -> User | None:
    record = _USERS.get(username)
    if not record:
        # Equal-cost work reduces username-enumeration timing differences.
        hashlib.pbkdf2_hmac("sha256", password.encode(), b"unknown-user", _PBKDF2_ITERATIONS)
        return None
    role, salt_hex, expected = record
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), _PBKDF2_ITERATIONS
    ).hex()
    return User(username=username, role=role) if hmac.compare_digest(actual, expected) else None


def create_access_token(user: User, expires_minutes: int | None = None) -> str:
    now = datetime.now(UTC)
    minutes = config.JWT_EXPIRES_MINUTES if expires_minutes is None else expires_minutes
    return jwt.encode(
        {"sub": user.username, "role": user.role.value, "iat": now, "exp": now + timedelta(minutes=minutes)},
        _SECRET,
        algorithm=config.JWT_ALGORITHM,
    )


def decode_token(token: str) -> User | None:
    """Return the user for a valid, unexpired token, otherwise None."""
    try:
        claims = jwt.decode(token, _SECRET, algorithms=[config.JWT_ALGORITHM])
        return User(username=claims["sub"], role=Role(claims["role"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    user = decode_token(credentials.credentials)
    if user is None:
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role is not Role.admin:
        raise HTTPException(403, f"Role '{user.role.value}' is not permitted for this action")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def authorize_action(user: User, action: str, matrix: dict[str, set[Role]]) -> None:
    """Raise 403 unless the user's role may perform the workflow action."""
    if user.role is Role.admin or user.role in matrix.get(action, set()):
        return
    raise HTTPException(403, f"Role '{user.role.value}' is not permitted to '{action}'")


def resolve_actor(user: User, claimed_actor: str | None) -> str:
    """Return the audit actor: always the authenticated identity.

    A body-supplied ``actor`` is accepted only for backwards compatibility and must
    match the token subject; a mismatch is rejected rather than silently recorded.
    """
    if claimed_actor is not None and claimed_actor != user.username:
        raise HTTPException(403, "actor must match the authenticated user")
    return user.username
