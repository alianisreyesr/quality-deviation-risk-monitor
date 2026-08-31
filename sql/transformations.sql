-- ---------------------------------------------------------------------------
-- Analytics-ready transformations over the operational tables.
--
-- These are SQL views (not materialized tables): SQLite recomputes them on
-- every query, so "today" and every derived flag always reflect the current
-- date — the same on-demand philosophy as app/data_quality.py and
-- app/metrics.py. A BI tool (Metabase — see docs/dashboard.md) or an ad-hoc
-- `sqlite3 data/quality_monitor.db` session can query these directly instead
-- of re-deriving overdue/aging logic per report.
--
-- Applied automatically by app/database.py on every startup (idempotent —
-- CREATE VIEW IF NOT EXISTS). A dbt/DuckDB pipeline would express the same
-- transformations as models; kept as plain SQL views here to stay in the
-- project's existing SQLite stack rather than adding a second engine for a
-- prototype of this size.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- fact_deviation_events
--
-- One row per deviation event, enriched with the derived analytical fields
-- a dashboard needs: overdue status, assignment status, days the record has
-- been open, and a numeric severity_weight aligned with app/scoring.py's
-- point values (kept in sync manually — see docs/risk-rules.md).
-- ---------------------------------------------------------------------------

DROP VIEW IF EXISTS fact_deviation_events;
CREATE VIEW fact_deviation_events AS
SELECT
    deviation_id,
    title,
    severity,
    CASE severity
        WHEN 'High'   THEN 3
        WHEN 'Medium' THEN 1
        ELSE 0
    END                                                     AS severity_weight,
    opened_date,
    due_date,
    investigation_owner,
    (investigation_owner IS NULL)                          AS is_unassigned,
    repeat_occurrence,
    record_complete,
    review_status,
    (review_status = 'Closed')                              AS is_closed,
    (review_status != 'Closed' AND date(due_date) < date('now'))
                                                             AS is_overdue,
    CASE
        WHEN review_status = 'Closed' THEN NULL
        ELSE CAST(julianday('now') - julianday(opened_date) AS INTEGER)
    END                                                      AS days_open
FROM deviations;

-- ---------------------------------------------------------------------------
-- fact_capa_lifecycle
--
-- One row per CAPA, spanning its full lifecycle from open to closure.
-- days_open freezes at days_to_close once a CAPA closes (mirrors
-- app/capa_scoring.compute_aging_days), so historical aging stays
-- meaningful instead of continuing to grow after closure.
-- ---------------------------------------------------------------------------

DROP VIEW IF EXISTS fact_capa_lifecycle;
CREATE VIEW fact_capa_lifecycle AS
SELECT
    capa_id,
    deviation_id,
    title,
    capa_type,
    severity,
    CASE severity
        WHEN 'High'   THEN 3
        WHEN 'Medium' THEN 1
        ELSE 0
    END                                                      AS severity_weight,
    root_cause,
    COALESCE(NULLIF(TRIM(root_cause), ''), 'Unspecified')    AS root_cause_bucket,
    opened_date,
    due_date,
    closure_date,
    owner,
    (owner IS NULL)                                          AS is_unassigned,
    recurrence_flag,
    effectiveness_check_complete,
    status,
    (status = 'Closed')                                      AS is_closed,
    (status != 'Closed' AND date(due_date) < date('now'))    AS is_overdue,
    -- effectiveness_check_complete may be stored as 0/1 or the literal text
    -- 'True'/'False' (see schema.sql's CHECK constraint) — SQLite does not
    -- coerce 'False' to falsy, so it is compared explicitly rather than
    -- negated with NOT.
    (status = 'Closed' AND effectiveness_check_complete NOT IN (1, 'True', 'true'))
                                                             AS closed_without_effectiveness_check,
    CASE
        WHEN status = 'Closed' AND closure_date IS NOT NULL
            THEN CAST(julianday(closure_date) - julianday(opened_date) AS INTEGER)
        WHEN status != 'Closed'
            THEN CAST(julianday('now') - julianday(opened_date) AS INTEGER)
        ELSE NULL
    END                                                      AS days_open
FROM capas;
