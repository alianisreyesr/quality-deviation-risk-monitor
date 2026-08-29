# Quality Deviation Risk Monitor

<div align="center">

[![CI](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/ci.yml)
[![CodeQL](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/codeql.yml/badge.svg)](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/codeql.yml)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-20232A?style=flat&logo=react&logoColor=61DAFB)
![SQLite](https://img.shields.io/badge/SQLite-audit%20trail-003B57?style=flat&logo=sqlite&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat&logo=pydantic&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?style=flat&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-112%20passing-brightgreen?style=flat)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

**GxP · CSV · 21 CFR Part 11 · ALCOA+ · Data Integrity · Audit Trail**

*A portfolio-safe, full-stack prototype for pharmaceutical Quality Data Engineering*

[Screenshots](#portfolio-preview) · [Quick Start](#quick-start) · [Case study](docs/CASE_STUDY.md) · [Architecture](docs/architecture.md) · [Risk Rules](docs/risk-rules.md) · [Security](SECURITY.md)

</div>

---

> **⚠️ Data Boundary:** Every record, name, and scenario is entirely fictional. This repository contains no proprietary information, employer data, processes, or code. It is not validated software and must not be used for regulated quality decisions.

---

## Portfolio preview

| Reviewer queue | Explainable review panel |
|---|---|
| ![Synthetic deviation reviewer queue with risk summary](docs/assets/dashboard.png) | ![Explainable risk panel showing contributing rules and human-review boundary](docs/assets/review-panel.png) |

See the [case study](docs/CASE_STUDY.md) for the business problem, users, decisions, evidence, and production boundary.

## What This Is

A **full-stack quality deviation prioritization system** that models how a data engineer approaches regulated backlog management: with traceable data pipelines, explainable rule-based scoring, and a tamper-evident audit trail aligned to 21 CFR Part 11 and ALCOA+.

In GxP manufacturing, unreviewed deviations accumulate regulatory risk. This prototype answers: *how do you surface the right record, at the right time, with full traceability?* — using transparent engineering instead of black-box ML.

**Built with:** Python · FastAPI · Pydantic v2 · SQLite · React · Vite · Docker · GitHub Actions CI

---

## Skills Demonstrated

> Mapped to job descriptions for **Quality Data Engineer**, **CSV Analyst**, and **IT Compliance** roles.

| Domain | What This Project Shows |
|---|---|
| **Data Pipeline & SQL** | Synthetic CSV → SQLite staging with schema constraints, indexes, and validated ingestion |
| **21 CFR Part 11 / Audit Trail** | Append-only `audit_log` table; `AuditMiddleware` logs every mutating HTTP request; UTC server-generated timestamps — never client-supplied |
| **ALCOA+ Data Integrity** | Attributable (actor header), Legible, Contemporaneous, Original, Accurate — modeled in schema and API layer |
| **Explainable Risk Scoring** | Rule-based, version-controlled scorer; every response returns `contributing_reasons[]` so reviewers can evaluate — not blindly accept — the output |
| **API Engineering** | FastAPI + Pydantic v2 with rate limiting (SlowAPI), structured error handling, and OpenAPI docs auto-generated |
| **Testing & CI** | 112 tests across 10 modules (unit + integration); GitHub Actions runs the full suite on every push |
| **Containerization** | Dockerfile + docker-compose for reproducible, environment-agnostic deployment |
| **Documentation** | Architecture, risk rules, **regulatory references (FDA / MHRA / PIC/S / EU)**, controls, known limitations, and CHANGELOG |

---

## Architecture

```mermaid
flowchart TD
    CSV[Synthetic CSV\nAll data is fictional]
    DB[(SQLite Staging\nschema + indexes)]
    RULES[Validation + Risk Rules\nexplainable · versioned]
    API["FastAPI Layer\n+ AuditMiddleware\n(logs every mutating request → audit_log)"]
    UI[React Dashboard\nreviewer UI]
    AUDIT[(audit_log table\nappend-only · tamper-evident)]
    DOCS[/docs UI\nSwagger/]

    CSV --> DB
    DB --> RULES
    RULES --> API
    API --> UI
    API --> AUDIT
    API --> DOCS
```

See [architecture and data lineage →](docs/architecture.md) · [Regulatory references →](docs/REGULATORY_REFERENCES.md)

---

## Quick Start

### Option A — Local (Python + Node)

```bash
# 1. Clone
git clone https://github.com/alianisreyesr/quality-deviation-risk-monitor.git
cd quality-deviation-risk-monitor

# 2. Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → API at http://127.0.0.1:8000
# → Swagger UI (interactive API docs) at http://127.0.0.1:8000/docs
# → ReDoc at http://127.0.0.1:8000/redoc

# 3. Frontend (new terminal)
cd frontend
npm install && npm run dev
# → Reviewer dashboard at http://127.0.0.1:5173
```

### Option B — Docker (one command)

```bash
docker compose up --build
```

---

## API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Service state + synthetic-data boundary confirmation |
| `/deviations` | GET | Scored deviations; filterable by `risk_level` and `review_status` |
| `/deviations/{id}` | GET | Single record with explainable `contributing_reasons[]` |
| `/deviations/{id}/review` | POST | Record review action (`acknowledge` / `investigate` / `close`) — appends to audit log |
| `/summary` | GET | Queue counts, overdue items, unassigned records |
| `/audit-log` | GET | Full immutable audit log, newest-first; filterable by `deviation_id` |
| `/cache/invalidate` | POST | Manual cache invalidation |

> Full interactive docs auto-generated at `/docs` (Swagger UI) and `/redoc` — run the project locally to explore.

---

## Risk Scoring Model

The score is **explainable, not predictive** — designed to assist reviewers, not replace their judgment. This mirrors the expectation in regulated environments where algorithmic decisions must be defensible.

| Signal | Points | Rationale |
|---|---|---|
| Severity = Critical | +3 | Highest regulatory exposure |
| Severity = Major | +2 | Significant process deviation |
| Past due | +2 | Overdue review creates backlog risk |
| Missing owner | +1 | Unassigned deviations stall investigation |
| Recurrence flag | +1 | Repeat issues indicate systemic failure |
| Incomplete record | +1 | Missing fields impede audit readiness |

**Thresholds:** `High` ≥ 5 · `Medium` 2–4 · `Low` 0–1

Every API response includes `contributing_reasons[]` — a list of human-readable strings explaining the score. Reviewers evaluate, not blindly accept, the prioritization.

See [risk rules and controls →](docs/risk-rules.md)

---

## Audit Trail Design (21 CFR Part 11 / ALCOA+)

Every `POST /deviations/{id}/review` appends one immutable row. `AuditMiddleware` also logs all mutating HTTP requests. The `audit_log` table is **never updated or deleted** — only inserted into.

| Field | Description |
|---|---|
| `actor` | Required reviewer identifier (`X-Actor` header) — Attributable |
| `action` | `acknowledge` / `investigate` / `close` / `METHOD /path` |
| `previous_status` / `new_status` | Before-and-after workflow state |
| `comment` | Optional rationale or request-body snapshot (max 1,000 chars) |
| `ip_address` / `user_agent` | Client traceability |
| `status_code` / `latency_ms` | HTTP metadata for middleware-logged events |
| `created_at` | UTC timestamp, server-generated — never client-supplied — Contemporaneous |

---

## Repository Structure

```mermaid
flowchart TB
  R["quality-deviation-risk-monitor"]
  R --> A["app — FastAPI, domain models, audit trail, and cache"]
  A --> AA["main.py and models.py — API and deviation contracts"]
  A --> AB["audit modules — append-only evidence and review routes"]
  A --> AC["cache.py — in-memory TTL cache"]
  R --> D["data — synthetic CSV inputs"]
  R --> F["frontend — Vite and React reviewer dashboard"]
  R --> S["sql — schema constraints and indexes"]
  R --> U["scripts — data generation and utilities"]
  R --> T["tests — API, audit, cache, database, middleware, models, and scoring"]
  R --> O["docs — architecture, risk rules, and regulatory references"]
  R --> P["Docker, contribution, security, changelog, and license files"]
```

---

## Test Suite

112 tests · 10 modules · runs on every push via GitHub Actions CI

```bash
pytest -q
```

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for the CI configuration.

---

## Scope & Production Path

This is a **learning and portfolio artifact** built to demonstrate GxP-relevant engineering patterns. Production use in a regulated environment would additionally require:

- Formal IQ/OQ/PQ validation with test protocols and sign-off
- Requirements Traceability Matrix (RTM)
- Role-based access control and user authentication
- Change control documentation and version locking
- Security assessment and penetration testing
- Governed SOPs and procedural controls

See [IMPROVEMENTS.md](IMPROVEMENTS.md) and [docs/REGULATORY_REFERENCES.md](docs/REGULATORY_REFERENCES.md).

---

## Regulated Portfolio Ecosystem

| Project | Domain Focus | Status |
|---|---|---|
| **[CSV Evidence Tracker](https://github.com/alianisreyesr/csv-evidence-tracker)** | Requirements traceability, IQ/OQ/PQ test execution, audit trail | ✅ Active · 44 tests |
| **[GxP Change Control](https://github.com/alianisreyesr/gxp-change-control)** | Controlled change lifecycle & approvals | ✅ Active · 68 tests |
| **[Data Integrity Case File](https://github.com/alianisreyesr/data-integrity-case-file)** | ALCOA+ investigation, CAPA readiness, local AI triage | ✅ Active |
| **[CSA Assurance Planner](https://github.com/alianisreyesr/csa-assurance-planner)** | Risk-based software assurance planning, FDA CSA alignment | ✅ Active |
| **[GxP Batch Data Pipeline](https://github.com/alianisreyesr/gxp-batch-data-pipeline)** | Batch manufacturing pipeline — DuckDB · dbt · quality gates | ✅ Active · 12 tests |

---

<div align="center">

**Built by [Alianis Reyes-Reyes](https://www.linkedin.com/in/alianis-reyes-reyes/)**

Information Systems @ UPRM · Eli Lilly Tech@Lilly Alumni

*Every iteration of this project is a question: what would make this more trustworthy, more traceable, more useful in a real regulated environment? That question doesn't have a final answer — and that's exactly what keeps it interesting.*

</div>
