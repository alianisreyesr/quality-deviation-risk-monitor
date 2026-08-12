CREATE TABLE IF NOT EXISTS deviations (
    deviation_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High')),
    opened_date TEXT NOT NULL CHECK (date(opened_date) IS NOT NULL),
    due_date TEXT NOT NULL CHECK (date(due_date) IS NOT NULL),
    investigation_owner TEXT,
    repeat_occurrence INTEGER NOT NULL CHECK (repeat_occurrence IN (0, 1, 'True', 'False')),
    record_complete INTEGER NOT NULL CHECK (record_complete IN (0, 1, 'True', 'False')),
    review_status TEXT NOT NULL CHECK (review_status IN ('Not Started', 'Pending Review', 'In Review', 'Escalated', 'Closed'))
);

CREATE INDEX IF NOT EXISTS idx_deviations_due_date ON deviations(due_date);
CREATE INDEX IF NOT EXISTS idx_deviations_review_status ON deviations(review_status);
