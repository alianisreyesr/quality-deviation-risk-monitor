# Local Demo Walkthrough

A scripted, ~5-minute walkthrough of the running API — useful as a live demo
script, or as the basis for a screen recording. Every command is safe to run
against the synthetic dataset; nothing here touches real data.

## 1. Start the API

```bash
git clone https://github.com/alianisreyesr/quality-deviation-risk-monitor.git
cd quality-deviation-risk-monitor
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Or, with Docker: `docker compose up --build`.

## 2. Health and version

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Shows `status`, the synthetic-data boundary confirmation, and `version` —
useful for confirming which build a deployed instance is running.

## 3. Explainable deviation risk

```bash
curl -s "http://127.0.0.1:8000/deviations?risk_level=High" | python3 -m json.tool | head -30
```

Point out `risk_score`, `risk_level`, `risk_reasons[]`, and
`scoring_rule_version` on a single record — the score is never a black box;
every point is traceable to a named rule in `docs/risk-rules.md`.

## 4. CAPA risk and aging

```bash
curl -s "http://127.0.0.1:8000/capas?risk_level=High" | python3 -m json.tool | head -40
```

Highlight `aging_days` (freezes at time-to-close once a CAPA closes — see
`app/capa_scoring.compute_aging_days`) and a `risk_reasons` entry like
`"Closed without a completed effectiveness check"` — a data-integrity signal
a naive severity-only score would miss entirely.

## 5. Data quality

```bash
curl -s http://127.0.0.1:8000/data-quality | python3 -m json.tool
curl -s http://127.0.0.1:8000/capas/data-quality | python3 -m json.tool
```

Unique-ID, required-field, valid-date, and allowed-value checks for both
datasets — the same checks a data engineer would run before trusting a
pipeline's output.

## 6. Quality metrics (dashboard-ready)

```bash
curl -s http://127.0.0.1:8000/metrics | python3 -m json.tool
```

Aging buckets, recurrence rate, severity distribution, CAPA closure rate,
and root-cause breakdown — the same figures `docs/dashboard.md` turns into a
Metabase dashboard.

## 7. Reviewer workflow + audit trail

```bash
curl -s -X POST http://127.0.0.1:8000/deviations/DEV-1002/review \
  -H "Content-Type: application/json" \
  -d '{"action": "acknowledge", "actor": "demo.reviewer", "comment": "Demo walkthrough"}' \
  | python3 -m json.tool

curl -s "http://127.0.0.1:8000/deviations/DEV-1002/audit-trail" | python3 -m json.tool
```

Shows the append-only audit event: actor, previous/new status, and a
server-generated UTC timestamp — never client-supplied.

## 8. Interactive API docs

Open `http://127.0.0.1:8000/docs` (Swagger UI) or `/redoc` — every endpoint
above, with request/response schemas, generated automatically from the
Pydantic models in `app/models.py`.

## 9. React reviewer dashboard (optional)

```bash
cd frontend && npm install && npm run dev
```

Open `http://127.0.0.1:5173` for the visual reviewer queue and the
explainable-risk detail panel (`docs/assets/dashboard.png`,
`docs/assets/review-panel.png`).

## 10. Fact tables (SQL layer)

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/quality_monitor.db')
for row in conn.execute('SELECT capa_id, status, days_open, root_cause_bucket FROM fact_capa_lifecycle ORDER BY days_open DESC LIMIT 5'):
    print(row)
"
```

The same views a BI tool queries directly — see `docs/dashboard.md` for the
Metabase setup and starter questions.
