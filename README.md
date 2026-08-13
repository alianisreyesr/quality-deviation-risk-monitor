# Quality Deviation Risk Monitor

<div align="center">

[![CI](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-20232A?style=flat&logo=react&logoColor=61DAFB)
![SQLite](https://img.shields.io/badge/SQLite-audit%20trail-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)
![Tests](https://img.shields.io/badge/tests-57%20passing-brightgreen?style=flat)

**GxP · CSV · 21 CFR Part 11 · ALCOA+ · Data Integrity · Audit Trail**

*A portfolio-safe, full-stack prototype for regulated quality environments*

</div>

---

> **⚠️ Data boundary:** Every record, name, and scenario is entirely fictional. This repository contains no proprietary information, employer data, processes, or code. It is not validated software and must not be used for regulated quality decisions.

---

## Overview

This system **prioritizes synthetic quality-deviation records** using transparent, rule-based risk signals. It demonstrates the intersection of data engineering, API design, explainable scoring, and 21 CFR Part 11-aligned audit trail design — the exact skill set required in pharmaceutical Quality Data Engineering and Computer System Validation (CSV) roles.

**Why this matters in pharma:** In regulated manufacturing environments, deviation backlog management is a critical quality process. Unreviewed deviations accumulate risk exposure. This prototype models how a data engineer approaches that problem: with traceable data pipelines, explainable scoring, and tamper-evident audit logs — not black-box ML.

---

## What It Demonstrates

| Capability | Implementation |
|---|---|
| **Data pipeline** | Synthetic CSV → SQLite staging with schema constraints and indexes |
| **API design** | FastAPI + Pydantic with rate limiting and structured error handling |
| **Explainable risk scoring** | Rule-based, version-controlled — returns contributing reasons per record |
| **Audit trail (21 CFR Part 11)** | Append-only `audit_log` table; actor + timestamp on every mutation |
| **API-level traceability** | `AuditMiddleware` logs every mutating HTTP request to `audit_log` |
| **Reviewer dashboard** | React + Vite with risk filters, search, and rationale panel |
| **Test coverage** | 57 automated tests across 8 modules; runs on every push via GitHub Actions |
| **Documentation** | Architecture, risk rules, controls, limitations, and CHANGELOG |

---

## Architecture

```text
┌─────────────────┐
│  Synthetic CSV  │  ← All data is fictional, non-confidential
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────────────┐
│  SQLite Staging │────▶│  Validation + Risk Rules  │
│  (schema + idx) │     │  (explainable, versioned) │
└─────────────────┘     └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │       FastAPI Layer        │
                         │  + AuditMiddleware (logs   │
                         │    every mutating request) │
                         └────────────┬─────────────┘
                                      │
              ┌───────────────────────┼──────────────────┐
              ▼                       ▼                  ▼
   ┌──────────────────┐   ┌───────────────────┐  ┌─────────────┐
   │  React Dashboard │   │   audit_log table │  │  /docs UI   │
   │  (reviewer UI)   │   │  (append-only,    │  │  (FastAPI   │
   └──────────────────┘   │   tamper-evident) │  │   Swagger)  │
                          └───────────────────┘  └─────────────┘
```

See [architecture and data lineage](docs/architecture.md) and [risk rules and controls](docs/risk-rules.md).

---

## Quick Start

### Option A — Local (Python + Node)

```bash
# Clone
git clone https://github.com/alianisreyesr/quality-deviation-risk-monitor.git
cd quality-deviation-risk-monitor

# Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → API docs at http://127.0.0.1:8000/docs

# Frontend (new terminal)
cd frontend
npm install && npm run dev
# → Dashboard at http://127.0.0.1:5173
```

### Option B — Docker

```bash
docker compose up --build
```

---

## API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Service state + synthetic-data boundary confirmation |
| `/deviations` | GET | Scored deviations; filterable by `risk_level` and `review_status` |
| `/deviations/{id}` | GET | Single explainable risk record with contributing reasons |
| `/deviations/{id}/review` | POST | Record review action (`acknowledge` / `investigate` / `close`) — appends to audit log |
| `/summary` | GET | Queue counts, overdue items, unassigned records |
| `/audit-log` | GET | Full immutable audit log, newest-first; filterable by `deviation_id` |
| `/cache/invalidate` | POST | Manual cache invalidation |

---

## Risk Scoring Model

The score is **explainable, not predictive** — designed to assist reviewers, not replace their judgment.

| Signal | Points | Rationale |
|---|---|---|
| Severity = Critical | +3 | Highest regulatory exposure |
| Severity = Major | +2 | Significant process deviation |
| Past due | +2 | Overdue review creates backlog risk |
| Missing owner | +1 | Unassigned deviations stall investigation |
| Recurrence flag | +1 | Repeat issues indicate systemic failure |
| Incomplete record | +1 | Missing fields impede audit readiness |

**Thresholds:** High ≥ 5 · Medium 2–4 · Low 0–1  
Every response includes `contributing_reasons[]` so reviewers can evaluate — not blindly accept — the prioritization.

---

## Audit Trail Design (21 CFR Part 11 / ALCOA+)

Every `POST /deviations/{id}/review` appends one immutable row. `AuditMiddleware` also logs all mutating HTTP requests. The table is **never updated or deleted** — only inserted into.

| Field | Description |
|---|---|
| `actor` | Required reviewer identifier (`X-Actor` header) |
| `action` | `acknowledge` / `investigate` / `close` / `METHOD /path` |
| `previous_status` / `new_status` | Before-and-after workflow state |
| `comment` | Optional rationale or request-body snapshot (max 1,000 chars) |
| `ip_address` / `user_agent` | Client traceability |
| `status_code` / `latency_ms` | HTTP metadata (middleware events) |
| `created_at` | UTC timestamp, server-generated — never client-supplied |

---

## Repository Structure

```text
quality-deviation-risk-monitor/
├── app/
│   ├── audit_db.py          ← audit_log DB helpers (append-only)
│   ├── audit_middleware.py  ← logs all mutating HTTP requests
│   ├── audit_models.py      ← Pydantic models for audit events
│   ├── audit_router.py      ← POST /review + GET /audit-log
│   ├── cache.py             ← in-memory TTL cache
│   ├── models.py            ← Pydantic models for deviations
│   └── main.py
├── data/                    ← Synthetic CSV; SQLite DB gitignored
├── frontend/                ← Vite + React reviewer dashboard
├── sql/                     ← Schema constraints and query indexes
├── tests/                   ← 57 tests across 8 modules
│   ├── test_api.py          ← Endpoint integration tests
│   ├── test_audit.py        ← Audit trail integration tests
│   ├── test_cache.py        ← Cache unit & endpoint tests
│   ├── test_database.py     ← Database loading tests
│   ├── test_middleware.py   ← AuditMiddleware tests
│   ├── test_models.py       ← Pydantic model validation tests
│   └── test_scoring.py      ← Risk-scoring unit tests
├── docs/                    ← Architecture, risk rules, controls
├── CHANGELOG.md
├── IMPROVEMENTS.md
├── Dockerfile
└── docker-compose.yml
```

---

## Test Suite

```bash
pytest -q
# 57 tests across 8 modules — runs on every push via GitHub Actions CI
```

GitHub Actions runs the full suite on every push and pull request. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Quality & Scope

This is a **learning and portfolio artifact**. Production use in a regulated environment would require:
- Formal IQ/OQ/PQ validation
- Requirements traceability matrix (RTM)
- Formal access control and role-based permissions
- Change control documentation
- Security assessment and penetration testing
- Governed quality procedures and SOPs

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for a documented list of planned enhancements and known limitations.

---

## Related Portfolio Projects

| Project | Focus | Repo |
|---|---|---|
| **CSV Evidence Tracker** | Requirements traceability, IQ/OQ/PQ test execution, audit trail | *Coming soon* |
| **Student Assembly Registration** | Role-based access, institutional validation, PHP + MySQL | *In progress* |

---

<div align="center">

**Built by [Alianis Reyes-Reyes](https://www.linkedin.com/in/alianis-reyes-reyes/)** — Information Systems @ UPRM · Former Eli Lilly Intern

*Building trusted systems from data to decision.*

</div>
