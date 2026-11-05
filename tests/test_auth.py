"""Authentication, role authorization, actor attribution and rate limiting."""
import importlib

import jwt
import pytest
from fastapi.testclient import TestClient

from app import auth, config
from app.audit_db import fetch_audit_log, update_deviation_status
from app.auth import Role, User, create_access_token
from app.database import fetch_capas, fetch_deviations
from app.main import app
from app.rate_limit import limiter
from tests.conftest import auth_headers

client = TestClient(app)


def _dev_id() -> str:
    dev_id = fetch_deviations()[0]["deviation_id"]
    update_deviation_status(dev_id, "Open")
    return dev_id


# --- login -----------------------------------------------------------------

def test_login_returns_token_with_configured_ttl():
    r = client.post("/auth/token", json={"username": "reviewer.demo", "password": "ReviewerDemo!2026"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == config.JWT_EXPIRES_MINUTES * 60
    assert body["user"] == {"username": "reviewer.demo", "role": "reviewer"}
    claims = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert claims["sub"] == "reviewer.demo" and claims["role"] == "reviewer"
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json() == body["user"]


def test_login_rejects_bad_credentials_without_leaking_which_part_was_wrong():
    wrong_pw = client.post("/auth/token", json={"username": "reviewer.demo", "password": "wrong-password"})
    unknown = client.post("/auth/token", json={"username": "nobody.demo", "password": "wrong-password"})
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()


def test_login_body_is_never_written_to_the_audit_log():
    client.post("/auth/token", json={"username": "reviewer.demo", "password": "ReviewerDemo!2026"})
    assert all("ReviewerDemo" not in str(e.get("comment")) for e in fetch_audit_log(limit=20))


@pytest.mark.parametrize("header", [None, "Bearer not-a-jwt", "Basic abc"])
def test_review_requires_valid_bearer_token(header):
    dev_id = _dev_id()
    headers = {"Authorization": header} if header else {}
    r = client.post(f"/deviations/{dev_id}/review", json={"action": "acknowledge"}, headers=headers)
    assert r.status_code == 401


def test_expired_and_tampered_tokens_are_rejected():
    dev_id = _dev_id()
    user = User(username="reviewer.demo", role=Role.reviewer)
    expired = create_access_token(user, expires_minutes=-1)
    forged = jwt.encode({"sub": "admin.demo", "role": "admin"}, "wrong-secret", algorithm="HS256")
    for token in (expired, forged):
        r = client.post(
            f"/deviations/{dev_id}/review",
            json={"action": "acknowledge"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 401


# --- attribution -----------------------------------------------------------

def test_audit_actor_comes_from_token_not_body_or_header():
    dev_id = _dev_id()
    r = client.post(
        f"/deviations/{dev_id}/review",
        json={"action": "acknowledge"},
        headers={**auth_headers("reviewer", "alice.reviewer"), "X-Actor": "mallory"},
    )
    assert r.status_code == 200
    assert r.json()["actor"] == "alice.reviewer"
    assert fetch_audit_log(deviation_id=dev_id, limit=1)[0]["actor"] == "alice.reviewer"


def test_body_actor_that_differs_from_token_is_rejected_even_for_admin():
    dev_id = _dev_id()
    before = len(fetch_audit_log(deviation_id=dev_id))
    r = client.post(
        f"/deviations/{dev_id}/review",
        json={"action": "acknowledge", "actor": "someone.else"},
        headers=auth_headers("admin", "admin.user"),
    )
    assert r.status_code == 403
    assert len(fetch_audit_log(deviation_id=dev_id)) == before


# --- roles -----------------------------------------------------------------

def test_reviewer_cannot_close_but_quality_manager_can():
    dev_id = _dev_id()
    denied = client.post(f"/deviations/{dev_id}/review", json={"action": "close"}, headers=auth_headers("reviewer"))
    assert denied.status_code == 403
    client.post(f"/deviations/{dev_id}/review", json={"action": "acknowledge"}, headers=auth_headers("reviewer"))
    allowed = client.post(f"/deviations/{dev_id}/review", json={"action": "close"}, headers=auth_headers("quality_manager"))
    assert allowed.status_code == 200


def test_capa_close_requires_quality_manager():
    capa_id = fetch_capas()[0]["capa_id"]
    r = client.post(f"/capas/{capa_id}/review", json={"action": "close"}, headers=auth_headers("reviewer"))
    assert r.status_code == 403
    r = client.post(f"/capas/{capa_id}/review", json={"action": "start"})
    assert r.status_code == 401


def test_cache_invalidate_is_admin_only():
    assert client.post("/cache/invalidate").status_code == 401
    assert client.post("/cache/invalidate", headers=auth_headers("quality_manager")).status_code == 403
    assert client.post("/cache/invalidate", headers=auth_headers("admin")).status_code == 200


def test_read_endpoints_remain_public():
    for path in ("/health", "/deviations", "/summary", "/capas", "/audit-log"):
        assert client.get(path).status_code == 200, path


# --- secret handling -------------------------------------------------------

def test_production_requires_strong_jwt_secret(monkeypatch):
    monkeypatch.setattr(config, "ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        auth._load_secret()
    monkeypatch.setenv("JWT_SECRET_KEY", "short")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        auth._load_secret()
    monkeypatch.setenv("JWT_SECRET_KEY", "k" * 40)
    assert auth._load_secret() == "k" * 40


def test_development_without_secret_warns_and_generates_one(monkeypatch):
    monkeypatch.setattr(config, "ENVIRONMENT", "development")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.warns(UserWarning, match="ephemeral"):
        assert len(auth._load_secret()) >= 32


def test_config_reads_environment_and_version(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", " Production ")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.ENVIRONMENT == "production"
    finally:
        monkeypatch.setenv("ENVIRONMENT", "test")
        importlib.reload(config)
    assert client.get("/health").json()["version"] == config.APP_VERSION


# --- rate limiting ---------------------------------------------------------

def test_read_endpoints_are_rate_limited_at_100_per_minute():
    limiter.enabled = True
    limiter.reset()
    codes = [client.get("/summary").status_code for _ in range(101)]
    assert codes[:100] == [200] * 100
    assert codes[100] == 429


def test_login_is_rate_limited():
    limiter.enabled = True
    limiter.reset()
    codes = [
        client.post("/auth/token", json={"username": "reviewer.demo", "password": "wrong-password"}).status_code
        for _ in range(11)
    ]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429


# --- deployment config consistency ----------------------------------------

def test_render_yaml_env_vars_match_what_the_app_reads():
    from pathlib import Path

    import yaml

    render = yaml.safe_load((Path(__file__).resolve().parent.parent / "render.yaml").read_text())
    env = {item["key"]: item for item in render["services"][0]["envVars"]}
    assert env["ENVIRONMENT"]["value"] in config.PRODUCTION_ENVIRONMENTS
    assert env["JWT_SECRET_KEY"].get("generateValue") is True
    assert "CORS_ORIGINS" in env and "ALLOWED_ORIGINS" not in env
