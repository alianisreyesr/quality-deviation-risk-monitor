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
                            'Not Started', 'Pending Review', 'In Review', 'Escalated', 'Closed'
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
