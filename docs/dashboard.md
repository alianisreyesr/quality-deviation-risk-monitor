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

SQLite is not one of Metabase's officially-supported production databases
(it isn't available on Metabase Cloud), but the self-hosted OSS Docker image
ships a SQLite driver **built in** — no third-party plugin jar is required
for this local, read-only, single-user dashboard over a portfolio-scale
SQLite file.

> **Correction (verified 2026-08-31):** earlier revisions of this doc pointed
> at a community driver, `AlexR2D2/metabase_sqlite_driver`, downloaded via
> `curl` into a bind-mounted `metabase-plugins/` directory. That repository
> and release no longer exist (the download URL now 404s), and it turns out
> to be unnecessary: `modules/drivers/sqlite` ships in the `metabase/metabase`
> image itself, so `Admin settings → Databases → Add database → SQLite` works
> with no extra setup. The `metabase-plugins/` bind mount in
> `docker-compose.yml` is harmless (Metabase loads any *additional* plugin
> jars placed there) but is no longer required — leave it empty or drop it.

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

## Verification status (2026-08-31)

The environment this doc was last revised in has no Docker daemon
available, so the following was verified **without** running the
containers:

- `docker compose config` and `docker compose --profile dashboard config`
  both parse and resolve cleanly (no schema errors, `metabase` service only
  appears under the `dashboard` profile as intended).
- `metabase/metabase:v0.50.8` exists on Docker Hub (`HEAD` on the tags API
  returns `200`).
- The previously-documented `AlexR2D2/metabase_sqlite_driver` release URL
  returns `404` — the repository no longer exists — and was removed above
  in favor of the driver Metabase ships built in.

- All eight "Starter questions" SQL statements above were executed directly
  against a freshly-seeded copy of `sql/schema.sql` +
  `sql/transformations.sql` via `sqlite3` (Python's stdlib driver, not
  Metabase) and each returned rows with no SQL errors.

**Not verified end-to-end in this pass:** actually bringing up
`docker compose --profile dashboard up --build`, adding
`/data/quality_monitor.db` as a SQLite database through the Metabase admin
UI, and running the starter questions as Metabase Questions against a live
instance — i.e. Metabase's own SQLite driver and query engine were not
exercised. Verify that with a Docker daemon available before relying on this
doc as fully runtime-tested.
