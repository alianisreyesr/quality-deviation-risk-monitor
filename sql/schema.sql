CREATE TABLE IF NOT EXISTS deviations (
    deviation_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High')),
    opened_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    investigation_owner TEXT,
    repeat_occurrence INTEGER NOT NULL CHECK (repeat_occurrence IN (0, 1)),
    record_complete INTEGER NOT NULL CHECK (record_complete IN (0, 1)),
    review_status TEXT NOT NULL
);
