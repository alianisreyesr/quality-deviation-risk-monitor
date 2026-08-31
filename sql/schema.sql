CREATE TABLE IF NOT EXISTS deviations (
    deviation_id        TEXT PRIMARY KEY,
    title               TEXT    NOT NULL,
    severity            TEXT    NOT NULL CHECK (severity IN ('Low', 'Medium', 'High')),
    opened_date         TEXT    NOT NULL CHECK (date(opened_date) IS NOT NULL),
    due_date            TEXT    NOT NULL CHECK (date(due_date) IS NOT NULL),
    investigation_owner TEXT,
    repeat_occurrence   INTEGER NOT NULL CHECK (repeat_occurrence IN (0, 1, 'True', 'False')),
    record_complete     INTEGER NOT NULL CHECK (record_complete IN (0, 1, 'True', 'False')),
    review_status       TEXT    NOT NULL CHECK (review_status IN (
                            'Open', 'Under Review', 'Investigation In Progress', 'Closed'
                        ))
);

-- ---------------------------------------------------------------------------
-- Single-column indexes: support equality filters on common query parameters
-- ---------------------------------------------------------------------------

-- Supports: GET /deviations?review_status=...
CREATE INDEX IF NOT EXISTS idx_deviations_review_status
    ON deviations(review_status);

-- Supports: ORDER BY / filter on due_date (overdue detection in /summary)
CREATE INDEX IF NOT EXISTS idx_deviations_due_date
    ON deviations(due_date);

-- Supports: scoring pass that reads severity for every record
CREATE INDEX IF NOT EXISTS idx_deviations_severity
    ON deviations(severity);

-- ---------------------------------------------------------------------------
-- Composite index: covers the most common combined filter pattern
-- GET /deviations?review_status=...  (with implicit ORDER BY due_date)
-- Also accelerates the /summary overdue + severity breakdown queries
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_deviations_status_due
    ON deviations(review_status, due_date);

-- ---------------------------------------------------------------------------
-- Note: risk_level (Low / Medium / High) is computed at query time in
-- app/scoring.py and is not stored as a column — no index applies.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- CAPA (Corrective and Preventive Action) records
--
-- A CAPA may originate from a deviation (deviation_id set) or be raised
-- independently (e.g. from a trend review). Lifecycle and risk scoring
-- mirror the deviations table so both record types can be prioritized and
-- reported on with the same explainable-rule approach.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS capas (
    capa_id                       TEXT PRIMARY KEY,
    deviation_id                  TEXT,
    title                         TEXT    NOT NULL,
    capa_type                     TEXT    NOT NULL CHECK (capa_type IN ('Corrective', 'Preventive')),
    severity                      TEXT    NOT NULL CHECK (severity IN ('Low', 'Medium', 'High')),
    root_cause                    TEXT,
    opened_date                   TEXT    NOT NULL CHECK (date(opened_date) IS NOT NULL),
    due_date                      TEXT    NOT NULL CHECK (date(due_date) IS NOT NULL),
    closure_date                  TEXT    CHECK (closure_date IS NULL OR date(closure_date) IS NOT NULL),
    owner                         TEXT,
    recurrence_flag               INTEGER NOT NULL CHECK (recurrence_flag IN (0, 1, 'True', 'False')),
    effectiveness_check_complete  INTEGER NOT NULL CHECK (effectiveness_check_complete IN (0, 1, 'True', 'False')),
    status                        TEXT    NOT NULL CHECK (status IN (
                                    'Open', 'In Progress', 'Pending Effectiveness Check', 'Closed'
                                   )),
    FOREIGN KEY (deviation_id) REFERENCES deviations(deviation_id)
);

-- Supports: GET /capas?status=... and closure-rate metrics
CREATE INDEX IF NOT EXISTS idx_capas_status
    ON capas(status);

-- Supports: aging / overdue detection in /capas summary and /metrics
CREATE INDEX IF NOT EXISTS idx_capas_due_date
    ON capas(due_date);

-- Supports: scoring pass that reads severity for every CAPA
CREATE INDEX IF NOT EXISTS idx_capas_severity
    ON capas(severity);

-- Supports: linking a CAPA back to its originating deviation
CREATE INDEX IF NOT EXISTS idx_capas_deviation_id
    ON capas(deviation_id);

-- Supports: root-cause breakdown metric (GET /metrics)
CREATE INDEX IF NOT EXISTS idx_capas_root_cause
    ON capas(root_cause);
