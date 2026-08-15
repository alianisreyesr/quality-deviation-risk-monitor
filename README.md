# Quality Deviation Risk Monitor

> Portfolio-safe quality analytics prototype for prioritizing synthetic deviation records through a transparent, risk-based workflow.

## Purpose

Quality teams often need to triage many deviation records before deciding which require immediate review. This project demonstrates a small, auditable decision-support workflow that ingests **synthetic** quality-deviation data, calculates and exposes risk-oriented signals, and presents the records through a FastAPI service and React dashboard.

It is designed as a portfolio demonstration of data engineering, API development, automated testing, and validation-aware documentation—not as a production quality-management system.

## Highlights

- **Synthetic data only:** No patient, product, manufacturing, or proprietary information is used.
- **Transparent decision support:** Risk prioritization is rule-based and intended to be inspectable in code and tests.
- **Full-stack workflow:** Python, SQL, FastAPI, React, Docker, and automated tests.
- **Quality-system awareness:** Documentation records intended use, scope, assumptions, verification evidence, and known limitations.
- **Portfolio safe:** Built to discuss GxP/CSV concepts without claiming validated production use.

## Architecture

```text
Synthetic CSV data
       |
       +-- SQL schema / data-loading script
       |
       v
FastAPI risk-monitoring API
       |
       v
React dashboard for prioritized review
```

See [Architecture](docs/architecture.md), [Data dictionary](docs/data-dictionary.md), and [Validation summary](docs/validation-summary.md).

## Stack

| Layer | Technologies |
| --- | --- |
| Data | CSV, SQL, Python |
| API | FastAPI, Uvicorn |
| UI | React, Vite |
| Testing | Pytest, FastAPI TestClient |
| Delivery | Docker, Docker Compose, GitHub Actions |

## Quick start

### Run the API locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the interactive API documentation at `http://127.0.0.1:8000/docs`.

### Run with Docker

```bash
docker compose up --build
```

### Run tests

```bash
pytest -q
```

### Run the dashboard

```bash
cd frontend
npm install
npm run dev
```

The dashboard expects the API to be running locally.

## Project structure

```text
app/                 FastAPI application and configuration
data/                Synthetic deviation dataset
docs/                Architecture, validation summary, data dictionary
frontend/            React dashboard
scripts/             Data-loading and utility scripts
sql/                 Relational schema
tests/               Automated API and risk-logic tests
.github/workflows/   Continuous-integration workflows
```

## Quality and validation boundary

This repository demonstrates validation-aware engineering practices; it is **not** a validated computerized system. It must not be used to make real GxP, product-release, patient-safety, or manufacturing-quality decisions. Any production deployment would require organization-specific requirements, risk assessment, change control, data governance, security controls, computer-system validation, and approved operating procedures.

## Skills demonstrated

- Quality-data modeling and traceability-oriented documentation
- Risk-based prioritization and explainable business rules
- Python, SQL, FastAPI, REST API design, React, and Docker
- Automated testing and CI-oriented software delivery
- CSV/GAMP 5, ALCOA+, and 21 CFR Part 11 awareness

## Portfolio narrative

**Resume-ready description:** Built a portfolio-safe quality deviation risk-monitoring prototype using synthetic data, Python, SQL, FastAPI, React, Docker, and automated tests. Created validation-aware artifacts to demonstrate risk-based quality analytics and compliant-system design awareness.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). This project is released under the [MIT License](LICENSE).
