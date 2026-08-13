# Changelog

All notable changes to this project are documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions
and uses [Semantic Versioning](https://semver.org/).

> **Scope note:** This is a portfolio learning artifact using synthetic data.
> It is not validated software and must not be used for regulated quality decisions.

---

## [Unreleased]

### Planned
- Async database driver (`aiosqlite`) for concurrent request handling
- CORS whitelist configuration for deployment hardening

---

## [1.0.0] — 2026-08-12

Initial public release. Full-stack prototype demonstrating regulated-quality data engineering
patterns with synthetic deviation records.

### Added

#### Core API (`app/`)
- `GET /health` — service state and synthetic-data boundary confirmation; validates database connectivity and returns degraded status if unreachable
- `GET /deviations` — returns all scored synthetic deviations with optional `risk_level` and `review_status` query filters
- `GET /deviations/{deviation_id}` — single explainable risk record with `risk_score`, `risk_level`, and `risk_reasons`
- `GET /summary` — queue counts, overdue items, and unassigned records
- `POST /cache/invalidate` — forces cache refresh; rate-limited to 10 requests/minute
- `POST /deviations/{deviation_id}/review` — records a review action (`acknowledge` / `investigate` / `close`) with actor and optional comment; appends an immutable audit event
- `GET /audit-log` — returns the full immutable audit log, newest-first; filterable by `deviation_id`
- Pydantic response models for all endpoints (`app/models.py`, `app/audit_models.py`)
- Explainable, version-controlled risk scoring (`app/scoring.py`): points for severity, past-due status, missing ownership, recurrence, and incomplete records; High ≥ 5, Medium 2–4, Low 0–1

#### Audit Trail (21 CFR Part 11 / ALCOA+)
- Immutable, append-only `audit_log` table — no UPDATE or DELETE ever issued; tamper-evident by design
- `app/audit_db.py` — database helpers for append-only audit event insertion
- `app/audit_models.py` — Pydantic models for audit events and log responses
- `app/audit_router.py` — `/review` and `/audit-log` endpoint handlers
- `AuditMiddleware` (`app/audit_middleware.py`) — logs every mutating HTTP request (method, path, actor, body snapshot, IP, User-Agent, status code, latency) to `audit_log`; actor resolved from request body `actor` field or `X-Actor` header; excluded paths: `/cache/invalidate`, `/docs`, `/openapi.json`, `/redoc`; audit failure never breaks the response
- Audit fields: `actor`, `action`, `previous_status`, `new_status`, `comment` (max 1 000 chars), `ip_address`, `user_agent`, `status_code`, `latency_ms`, `created_at` (UTC)

#### Database
- SQL indexes on `severity`, `risk_level`, `due_date`, and `review_status` columns for query performance on filtered `/deviations` calls (`sql/`)
- SQLite staging database seeded from synthetic CSV on first start (`data/`)
- Schema constraints and query structure documented in `sql/`
- 30 synthetic deviation records — all fictional; no proprietary or employer data

#### Security
- Per-IP rate limiting via `slowapi`: 100 requests/minute on general endpoints, 10/minute on cache invalidation
- Input validation: `risk_level` filter restricted to `Low | Medium | High` via regex pattern
- Graceful error handling — database internals never exposed in responses
- HTTP status codes: 404 (missing resource), 422 (validation), 429 (rate limit), 500 (server error)

#### Performance
- In-memory TTL cache (`app/cache.py`, default 5-minute TTL) — reduces repeated scoring calculations; ~22× faster on cached `/deviations`, ~16× on cached `/summary`
- Lazy-loaded SQLite connection with `row_factory` for efficient dict mapping
- Prepared statements for SQL injection prevention

#### Observability
- Centralized logging (`app/logger.py`): console + rotating file handler (5 MB, 5 backups) at `logs/app.log`
- Log format: `timestamp | module | level | [file:line] | message`
- Config module (`app/config.py`) for environment-level settings

#### Frontend
- Vite + React reviewer dashboard (`frontend/`)
- Risk-level filter, search, and rationale panel
- Development proxy forwards `/api` requests to FastAPI

#### Testing & CI
- 57 automated tests across 8 modules (`tests/`): `test_api.py`, `test_audit.py`, `test_cache.py`, `test_database.py`, `test_main.py`, `test_middleware.py`, `test_models.py`, `test_scoring.py`
- `pytest --cov=app --cov-report=term-missing` coverage reporting
- GitHub Actions CI (`ci.yml`) — runs on every push and pull request
- GitHub Actions test workflow (`tests.yml`)

#### Documentation
- `README.md` with architecture diagram, run instructions, endpoint table, and risk model explanation
- `IMPROVEMENTS.md` with implementation details, benchmarks, and tuning guide
- `docs/architecture.md` — data lineage and component overview
- `docs/risk-rules.md` — scoring rule definitions and rationale
- `docs/validation-strategy.md` — test approach and non-production scope
- `docs/requirements-traceability-matrix.md` — RTM linking requirements to implementation
- `docs/portfolio-case-study.md` — narrative for recruiter and interview context
- `docs/release-checklist.md` — gate criteria for future releases
- `docs/implementation-plan.md` — development phasing and design decisions
- `docs/DATABASE_OPTIMIZATIONS.md` — index and connection pooling recommendations
- `Dockerfile` and `docker-compose.yml` for containerized local execution

### Technical Stack

| Layer | Technology |
|-------|------------|
| API framework | FastAPI 0.115.6 |
| Server | Uvicorn 0.32.1 |
| Validation | Pydantic 2.10.3 |
| Database | SQLite (synthetic data only) |
| Rate limiting | slowapi 0.1.9 |
| Testing | pytest 8.3.4 + httpx 0.28.1 |
| Frontend | Vite + React |
| CI | GitHub Actions |
| Containerization | Docker + docker-compose |

---

## Version Policy

This project uses **Semantic Versioning**:
- `MAJOR` — breaking API changes
- `MINOR` — new backward-compatible features
- `PATCH` — bug fixes and documentation updates

Because this is a portfolio artifact, version bumps are intentional and documented here
rather than tied to production release gates.

---

[Unreleased]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/releases/tag/v1.0.0
