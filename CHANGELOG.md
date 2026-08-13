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

## [1.2.0] — 2026-08-13

Implements Issue #4: full reviewer workflow with state-transition validation, a per-deviation audit trail endpoint, and 20 new targeted tests.

### Added

#### State Transition Validation
- `ALLOWED_TRANSITIONS` map in `audit_router.py` — defines which actions are permitted from each `review_status`. Prevents illogical moves (e.g. re-acknowledging a deviation already Under Review) and enforces `Closed` as a terminal state
- HTTP **409 Conflict** response when a requested action is not permitted; response body includes `current_status`, `requested_action`, and `allowed_actions` so callers know exactly what to do next
- `TransitionRejectedResponse` Pydantic model added to `audit_models.py`
- Transition table:
  - `Open` → `acknowledge` (→ Under Review), `investigate` (→ Investigation In Progress)
  - `Under Review` → `investigate`, `close` (→ Closed)
  - `Investigation In Progress` → `close`
  - `Closed` → *(terminal — no actions permitted)*

#### New Endpoint
- `GET /deviations/{deviation_id}/audit-trail` — returns the full audit event history for a single deviation, newest-first, with `current_review_status` and `event_count`; rate-limited to 60/minute; returns 404 for unknown deviation IDs
- `AuditTrailResponse` Pydantic model added to `audit_models.py`

#### New DB Helper
- `fetch_deviation_current_status(deviation_id)` in `audit_db.py` — read-only status lookup used by the transition validator before any write occurs; separates the read phase from the write phase for clarity

#### Tests (`tests/test_review_workflow.py` — 20 new tests)
- Valid transitions: all 5 permitted paths covered
- Blocked transitions: `Closed` state (all 3 actions → 409), `Under Review` re-acknowledge (409), `Investigation In Progress` acknowledge and re-investigate (409)
- 409 response body: `deviation_id`, `current_status`, `requested_action`, `allowed_actions` validated
- `GET /deviations/{id}/audit-trail`: 200 shape, 404 for unknown ID, event count increments after action
- Input validation: missing actor → 422, invalid action → 422
- Comment stored and returned correctly
- Blocked transition does **not** write to audit log (immutability guarantee)

### Changed
- `audit_router.py` — `review_deviation` now calls `fetch_deviation_current_status` first, then validates the transition, then calls `update_deviation_status`; removed inline `datetime` import workaround, now uses top-level import
- `audit_db.py` — added `fetch_deviation_current_status` helper

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
- `GET /audit-log` — returns the full immutable audit trail, newest-first; filterable by `deviation_id`
- Pydantic response models for all endpoints (`app/models.py`, `app/audit_models.py`)
- Explainable, version-controlled risk scoring (`app/scoring.py`): points for severity, past-due status, missing ownership, recurrence, and incomplete records; High ≥ 5, Medium 2–4, Low 0–1

#### Audit Trail (21 CFR Part 11 / ALCOA+)
- Immutable, append-only `audit_log` table — no UPDATE or DELETE ever issued; tamper-evident by design
- `app/audit_db.py` — database helpers for append-only audit event insertion
- `app/audit_models.py` — Pydantic models for audit events and log responses
- `app/audit_router.py` — `/review` and `/audit-log` endpoint handlers
- `AuditMiddleware` (`app/audit_middleware.py`) — logs every mutating HTTP request

#### Database
- SQL indexes on `severity`, `risk_level`, `due_date`, and `review_status` columns
- SQLite staging database seeded from synthetic CSV on first start
- 30 synthetic deviation records — all fictional; no proprietary or employer data

#### Security
- Per-IP rate limiting via `slowapi`
- Input validation and graceful error handling

#### Testing & CI
- 57 automated tests across 8 modules
- GitHub Actions CI on every push

#### Documentation
- Full README, architecture docs, risk rules, RTM, changelog, and case study
- Dockerfile + docker-compose

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

[Unreleased]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/releases/tag/v1.0.0
