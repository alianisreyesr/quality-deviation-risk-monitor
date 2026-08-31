# Initial Dashboard — Quality Deviation Risk Monitor

> Portfolio scope: this documents a **local, manually-built starter dashboard**
> in Metabase over the same SQLite database the API uses — not a hosted or
> automated BI deployment. It exists to show the analytics layer
> (`sql/transformations.sql`) is dashboard-ready, not to replace `GET /metrics`.

## Why Metabase, and why it's optional

Metabase is not part of the default `docker compose up` — it sits behind the
`dashboard` Compose profile so the API's CI smoke test and everyday local
runs stay fast. Start it explicitly when you want the dashboard:

```bash
docker compose --profile dashboard up --build
```

Metabase's official Docker image does not ship a SQLite driver (SQLite isn't
one of its supported production databases). For a **local, read-only,
single-user dashboard over a portfolio-scale SQLite file**, the community
[`metabase_sqlite_driver`](https://github.com/AlexR2D2/metabase_sqlite_driver)
plugin works well. One-time setup before the first `docker compose up`:

```bash
mkdir -p metabase-plugins
curl -L -o metabase-plugins/sqlite.metabase-driver.jar \
  https://github.com/AlexR2D2/metabase_sqlite_driver/releases/download/0.2.15/sqlite.metabase-driver.jar
```

`metabase-plugins/` is bind-mounted into the container at `/plugins` and is
already covered by `.gitignore` — driver binaries aren't checked into the
repo. If a newer Metabase image tag or driver release is out, pin both
together and update the version in `docker-compose.yml`.

## First-time setup

1. `docker compose --profile dashboard up --build`
2. Open `http://localhost:3000` and complete Metabase's setup wizard
   (creates a **local-only** admin account — not a real credential, this is
   a portfolio demo instance).
3. **Admin settings → Databases → Add database**
   - Database type: `SQLite`
   - Database file: `/data/quality_monitor.db`
   - This is the same file `app/database.py` seeds and the same
     `fact_deviation_events` / `fact_capa_lifecycle` views
     `sql/transformations.sql` creates — see [architecture](architecture.md)
     and [risk rules](risk-rules.md) for how the numbers are derived.

## Starter questions

Build each as a Metabase "Question" (SQL mode) against the database added
above, then pin them to a new dashboard named **Quality Deviation Risk
Monitor**.

| Question | SQL | Suggested visualization |
|---|---|---|
| Open deviations by severity | `SELECT severity, COUNT(*) AS open_count FROM fact_deviation_events WHERE is_closed = 0 GROUP BY severity;` | Bar |
| Overdue vs. on-time (open deviations) | `SELECT is_overdue, COUNT(*) AS n FROM fact_deviation_events WHERE is_closed = 0 GROUP BY is_overdue;` | Pie |
| Deviation aging distribution | `SELECT CASE WHEN days_open > 60 THEN '> 60d' WHEN days_open > 30 THEN '31-60d' ELSE '0-30d' END AS aging_bucket, COUNT(*) AS n FROM fact_deviation_events WHERE is_closed = 0 GROUP BY aging_bucket;` | Bar |
| CAPA closure rate | `SELECT status, COUNT(*) AS n FROM fact_capa_lifecycle GROUP BY status;` | Pie |
| CAPA closed without effectiveness check | `SELECT COUNT(*) AS n FROM fact_capa_lifecycle WHERE closed_without_effectiveness_check = 1;` | Number |
| Root cause breakdown | `SELECT root_cause_bucket, COUNT(*) AS n FROM fact_capa_lifecycle GROUP BY root_cause_bucket ORDER BY n DESC;` | Bar |
| Average CAPA time-to-close | `SELECT ROUND(AVG(days_open), 1) AS avg_days_to_close FROM fact_capa_lifecycle WHERE is_closed = 1;` | Number |
| CAPA aging (open only) | `SELECT capa_id, title, severity, days_open FROM fact_capa_lifecycle WHERE is_closed = 0 ORDER BY days_open DESC LIMIT 10;` | Table |

These mirror the same figures `GET /metrics` returns — the dashboard exists
for visual exploration; the API endpoint exists for programmatic / CI
consumption. Keep both in sync if a metric definition changes (see
`docs/rule-change-template.md`).

## Refreshing the data

The dashboard reads the live SQLite file, so re-running `pytest` or
restarting the `api` service (which reseeds an empty database) is reflected
the next time a Metabase question is re-run — no separate ETL step for this
prototype's scale.

## Known limitations

- SQLite via a community driver is a local/demo pattern only — Metabase's
  own docs recommend Postgres/MySQL for multi-user or production dashboards.
- No dashboard provisioning-as-code here (Metabase supports this via its API
  or serialization export, which is a reasonable next step — see
  [IMPROVEMENTS.md](../IMPROVEMENTS.md)).
- The Metabase admin account created in step 2 is local-only and gated
  behind the `dashboard` Compose profile — it is never part of the default
  `docker compose up` or CI.
