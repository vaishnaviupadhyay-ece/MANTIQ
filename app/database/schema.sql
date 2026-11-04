
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_code TEXT NOT NULL UNIQUE,
    bearing INTEGER NOT NULL CHECK (bearing BETWEEN 1 AND 4),
    machine_name TEXT NOT NULL DEFAULT 'NASA IMS Bearing Test Rig',
    severity TEXT NOT NULL CHECK (severity IN ('WARNING', 'CRITICAL')),
    status TEXT NOT NULL DEFAULT 'NEW'
        CHECK (status IN (
            'NEW',
            'ACKNOWLEDGED',
            'UNDER MAINTENANCE',
            'RESOLVED',
            'VERIFIED'
        )),
    created_at TEXT NOT NULL,
    recording_timestamp TEXT NOT NULL,
    anomaly_score REAL,
    condition_label TEXT NOT NULL,
    operator_findings TEXT,
    assigned_to TEXT,
    corrective_action TEXT,
    escalated INTEGER NOT NULL DEFAULT 0,
    resolved_at TEXT,
    verified_at TEXT
);

CREATE TABLE IF NOT EXISTS alert_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    role TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

CREATE TABLE IF NOT EXISTS maintenance_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    assigned_to TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    instructions TEXT,
    assigned_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

CREATE INDEX IF NOT EXISTS idx_alerts_status
ON alerts(status);

CREATE INDEX IF NOT EXISTS idx_alerts_bearing
ON alerts(bearing);

CREATE INDEX IF NOT EXISTS idx_activity_alert
ON alert_activity(alert_id);
