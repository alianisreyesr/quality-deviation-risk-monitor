CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    deviation_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('acknowledge', 'investigate', 'close')),
    actor TEXT NOT NULL,
    comment TEXT,
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deviation_id) REFERENCES deviations(deviation_id)
);

CREATE INDEX IF NOT EXISTS idx_audit_events_deviation_id
ON audit_events(deviation_id, event_id);
