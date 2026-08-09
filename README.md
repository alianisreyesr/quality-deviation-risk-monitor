# Quality Deviation Risk Monitor

A portfolio-safe prototype that turns synthetic quality-deviation records into transparent, rule-based risk signals. It demonstrates how data engineering, data integrity, and human review can support proactive quality oversight in regulated environments.

> **Confidentiality notice:** This project uses fictional data and simplified rules created exclusively for portfolio purposes. It does not contain proprietary information, code, processes, or data from any current or former employer.

## Why this project

Quality teams often need to prioritize open deviations before periodic reporting cycles. This prototype provides a lightweight, explainable view of open records based on due-date status, severity, investigation progress, recurrence, and data-completeness checks.

## What it demonstrates

- Python and FastAPI REST API design
- SQL schema design and data-quality validation
- Transparent, explainable rule-based risk scoring
- Synthetic data handling and field-level data dictionary
- Human-in-the-loop review status
- Portfolio-safe documentation for regulated contexts

## Architecture

```text
Synthetic CSV → SQLite staging table → validation + risk rules → FastAPI endpoints → reviewer-ready JSON output
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to test the API.

## API endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Confirms the API is running |
| `GET /deviations` | Returns all synthetic deviations with risk signals |
| `GET /deviations?risk_level=High` | Filters deviations by risk level |
| `GET /summary` | Returns counts by risk level and review status |

## Risk rules

The score is deliberately explainable rather than predictive. A record receives points when it is high severity, overdue, lacks an investigation owner, is a repeat occurrence, or has incomplete required data. The API returns the reasons alongside each score so a qualified reviewer can assess—not blindly accept—the prioritization.

## Data dictionary

| Field | Description |
| --- | --- |
| `deviation_id` | Synthetic unique record identifier |
| `severity` | Low, Medium, or High impact classification |
| `due_date` | Target date for investigation closure |
| `investigation_owner` | Assigned reviewer or owner |
| `repeat_occurrence` | Whether a similar event has recurred |
| `record_complete` | Whether required portfolio fields are populated |
| `review_status` | Human review workflow state |

## Roadmap

- [ ] Add automated tests for validation and scoring rules
- [ ] Add a simple React review interface
- [ ] Add data lineage diagram and decision log
- [ ] Containerize with Docker

## Tech stack

Python · FastAPI · SQLite · SQL · CSV · Pydantic
