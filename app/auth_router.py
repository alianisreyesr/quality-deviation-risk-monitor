"""Authentication endpoints: POST /auth/token and GET /auth/me."""

from fastapi import APIRouter, HTTPException, Request

from app.auth import (
    ACCESS_TOKEN_TTL_SECONDS,
    CurrentUser,
    LoginRequest,
    TokenResponse,
    User,
    authenticate,
    create_access_token,
)
from app.logger import setup_logger
from app.rate_limit import LOGIN_LIMIT, limiter

logger = setup_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse, summary="Obtain a bearer token")
@limiter.limit(LOGIN_LIMIT)
def login(request: Request, body: LoginRequest) -> TokenResponse:
    user = authenticate(body.username, body.password)
    if user is None:
        # Control characters are stripped so attacker-supplied names cannot forge log lines.
        safe_name = "".join(ch for ch in body.username if ch.isprintable())[:80]
        logger.warning("Failed login for %r", safe_name)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return TokenResponse(
        access_token=create_access_token(user),
        expires_in=ACCESS_TOKEN_TTL_SECONDS,
        user=user,
    )


@router.get("/me", response_model=User, summary="Identity of the current token")
def me(user: CurrentUser) -> User:
    return user
