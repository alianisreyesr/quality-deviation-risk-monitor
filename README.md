# Quality Deviation Risk Monitor

[![CI](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/alianisreyesr/quality-deviation-risk-monitor/actions/workflows/ci.yml)

A portfolio-safe, full-stack prototype that prioritizes **synthetic quality-deviation records** with transparent, rule-based risk signals. It demonstrates data engineering, API design, explainable prioritization, and control-oriented documentation for regulated-quality contexts.

> **Data boundary:** Every record, name, and scenario is fictional. This repository contains no proprietary information, employer data, processes, or code. It is not validated software and must not be used for regulated quality decisions.

## What it demonstrates

- SQLite staging and structured SQL constraints
- FastAPI endpoints with Pydantic response models
- Explainable, version-controlled risk scoring
- React reviewer dashboard with risk filters, search, and rationale panel
- Automated tests and GitHub Actions CI
- Human-review and non-production boundaries documented explicitly

## Architecture

```text
Synthetic CSV → SQLite staging → validation + risk rules → FastAPI → React reviewer dashboard
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

Open `http://127.0.0.1:8000/docs` for interactive API documentation. On first start, the local SQLite database is seeded from the synthetic CSV.

### Dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://127.0.0.1:5173`. The development proxy forwards `/api` requests to FastAPI.

## API endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Confirms service state and synthetic-data boundary |
| `GET /deviations` | Returns scored synthetic deviations |
| `GET /deviations?risk_level=High` | Filters the queue by calculated risk |
| `GET /deviations?review_status=Pending%20Review` | Filters the queue by workflow state |
| `GET /deviations/{deviation_id}` | Returns one explainable risk record |
| `GET /summary` | Returns queue counts, overdue items, and unassigned records |

## Risk model

The score is deliberately **explainable**, not predictive. The service assigns points for severity, past-due status, missing ownership, recurrence, and incomplete records. A High score is 5 or more, Medium is 2–4, and Low is 0–1. Each response returns the contributing reasons so that a reviewer can evaluate—not blindly accept—the prioritization.

## Repository structure

```text
app/        FastAPI, SQLite loading, schemas, and scoring rules
data/       Synthetic CSV source; generated SQLite database is ignored
frontend/   Vite + React reviewer dashboard
sql/        Schema constraints and query indexes
tests/      Automated behavior tests
docs/       Architecture, risk rules, controls, and limitations
```

## Quality and scope

`pytest -q` runs automated tests locally, and GitHub Actions runs them on every push and pull request. The project is intentionally scoped as a learning artifact; production use would require formal validation, requirements traceability, access control, audit trails, change control, security assessment, and governed quality procedures.
