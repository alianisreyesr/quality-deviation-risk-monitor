# Quality Deviation Risk Monitor

[![CI](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/ci.yml)

A portfolio-safe, full-stack prototype that prioritizes **synthetic quality-deviation records** with transparent, rule-based risk signals. It demonstrates data engineering, API design, explainable prioritization, 21 CFR Part 11-aligned audit trails, and control-oriented documentation for regulated-quality contexts.

> **Data boundary:** Every record, name, and scenario is fictional. This repository contains no proprietary information, employer data, processes, or code. It is not validated software and must not be used for regulated quality decisions.

## What it demonstrates

- SQLite staging and structured SQL constraints
- FastAPI endpoints with Pydantic response models and rate limiting
- Explainable, version-controlled risk scoring
- **Immutable audit trail** — append-only `audit_log` table, actor + timestamp on every mutation, 21 CFR Part 11 / ALCOA+ aligned
- `AuditMiddleware` — logs every mutating HTTP request (method, path, status, latency) to the same `audit_log` table for full API-level traceability
- React reviewer dashboard with risk filters, search, and rationale panel
- Automated tests (45 tests across 7 modules) and GitHub Actions CI
- Human-review and non-production boundaries documented explicitly

## Architecture

```text
Synthetic CSV → SQLite staging → validation + risk rules → FastAPI → React reviewer dashboard
                                          ↓
                                   audit_log table (append-only)
                                          ↑
                                   AuditMiddleware (every mutating request)
```

See [architecture and data lineage](docs/architecture.md) and [risk rules and controls](docs/risk-rules.md).

## Run locally

### API

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. On first start, the local SQLite database is seeded from the synthetic CSV and the `audit_log` table is created automatically.

### Dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://127.0.0.1:5173`. The development proxy forwards `/api` requests to FastAPI.

## API endpoints

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/health` | GET | Confirms service state and synthetic-data boundary |
| `/deviations` | GET | Returns scored synthetic deviations; filterable by `risk_level` and `review_status` |
| `/deviations/{deviation_id}` | GET | Returns one explainable risk record |
| `/deviations/{deviation_id}/review` | POST | Records a review action (`acknowledge` / `investigate` / `close`) with actor and optional comment; updates status and appends an immutable audit event |
| `/summary` | GET | Returns queue counts, overdue items, and unassigned records |
| `/audit-log` | GET | Returns the full immutable audit log, newest-first; filterable by `deviation_id` |
| `/cache/invalidate` | POST | Manually invalidates the scored-deviations cache (excluded from audit logging) |

## Risk model

The score is deliberately **explainable**, not predictive. The service assigns points for severity, past-due status, missing ownership, recurrence, and incomplete records. A High score is 5 or more, Medium is 2–4, and Low is 0–1. Each response returns the contributing reasons so that a reviewer can evaluate—not blindly accept—the prioritization.

## Audit trail

Every `POST /deviations/{id}/review` call appends one row to `audit_log`. The `AuditMiddleware` additionally logs every other mutating HTTP request to the same table. The table is never updated or deleted—only inserted into—making it tamper-evident. Each row captures:

| Field | Description |
| --- | --- |
| `actor` | Required identifier of the person taking the action (or `X-Actor` header fallback) |
| `action` | `acknowledge`, `investigate`, `close`, or `METHOD /path` for middleware events |
| `previous_status` / `new_status` | Before-and-after workflow state (review events only) |
| `comment` | Optional free-text rationale or request-body snapshot (max 1 000 chars) |
| `ip_address` / `user_agent` | Client traceability |
| `status_code` / `latency_ms` | HTTP response code and latency (middleware events) |
| `created_at` | UTC timestamp, server-generated |

## Repository structure

```text
app/        FastAPI, SQLite loading, schemas, scoring rules, and audit trail
              audit_db.py         — audit_log DB helpers (append-only)
              audit_middleware.py — logs all mutating HTTP requests
              audit_models.py     — Pydantic models for audit events
              audit_router.py     — POST /review and GET /audit-log endpoints
              cache.py            — in-memory TTL cache for scored deviations
data/       Synthetic CSV source; generated SQLite database is ignored
frontend/   Vite + React reviewer dashboard
sql/        Schema constraints and query indexes
tests/      Automated behavior tests (45 tests across 7 modules)
              test_api.py         — endpoint integration tests
              test_audit.py       — audit trail integration tests
              test_cache.py       — cache unit & endpoint tests
              test_database.py    — database loading tests
              test_main.py        — scoring determinism + API smoke tests
              test_middleware.py  — AuditMiddleware + path-parsing tests
              test_scoring.py     — risk-scoring unit tests
docs/       Architecture, risk rules, controls, and limitations
```

## Quality and scope

`pytest -q` runs the full test suite locally; GitHub Actions runs it on every push and pull request. The project is intentionally scoped as a learning artifact. Production use would require formal validation, requirements traceability, access control, change control, security assessment, and governed quality procedures.
