# Architecture and Data Lineage

## Purpose

This document explains how synthetic records move through the portfolio prototype. It is intentionally lightweight and designed to make assumptions and rule decisions visible to a reviewer.

## Data flow

```text
[Synthetic CSV]
      |
      v
[app/db.py — init_db()]
      |  Creates SQLite schema from sql/schema.sql
      |  Seeds deviations table from CSV on first run
      v
[SQLite — deviations.db]
      |
      v
[app/db.py — fetch_all_deviations()]
      |  Returns raw rows as dicts
      v
[app/scoring.py — score_deviation()]
      |  Applies transparent, rule-based risk logic
      |  severity + due date + owner + recurrence + completeness
      v
[app/main.py — FastAPI endpoints]
      |  /health  /deviations  /summary
      |  Pydantic response models enforce output schema
      v
[React frontend — DeviationTable + DetailPanel]
      |  Reviewer sees risk level, score, and reasons
      v
[Human reviewer — remains accountable for all decisions]
```

## Module responsibilities

| Module | Responsibility |
|---|---|
| `app/db.py` | SQLite connection, schema init, CSV seed, data fetch |
| `app/scoring.py` | Stateless risk-scoring logic; no I/O dependencies |
| `app/models.py` | Pydantic schemas for request validation and response typing |
| `app/main.py` | FastAPI app wiring, lifespan hooks, endpoint definitions |
| `sql/schema.sql` | Single source of truth for table structure |
| `data/deviations.csv` | Synthetic source data (30 records, portfolio-safe) |
| `frontend/src/main.jsx` | React reviewer dashboard — read-only, no writes to API |

## Control-oriented design choices

| Design choice | Why it matters |
|---|---|
| Synthetic source data | Keeps the public portfolio independent of employer information |
| Separated scoring module | Scoring logic is unit-testable without touching the database or HTTP layer |
| Pydantic response models | Output schema is typed and validated — no silent field drift |
| Explainable rule output | Shows the reason for each risk signal rather than hiding logic in a black box |
| Human review status | Keeps prioritization advisory; a reviewer remains accountable for decisions |
| Version-controlled rules | Changes to scoring logic are reviewable through Git history |
| GitHub Actions CI | Tests run automatically on every push — prevents silent regressions |

## Data-quality checks

The current prototype evaluates completeness via `record_complete` and applies field-level boolean coercion in `app/scoring.py` to handle both CSV strings (`"True"`/`"False"`) and native Python booleans. A future iteration can replace the single-flag indicator with per-field validation and test evidence consistent with a data integrity protocol.

## Non-production scope

This is a learning and portfolio project. It is not validated software, does not manage real quality records, and should not be used to make regulated quality decisions.
