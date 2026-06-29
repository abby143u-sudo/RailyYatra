CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL DEFAULT 'dry-run',
    status TEXT NOT NULL DEFAULT 'pending',
    source_name TEXT,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    records_seen INTEGER NOT NULL DEFAULT 0,
    records_accepted INTEGER NOT NULL DEFAULT 0,
    records_rejected INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_source_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingestion_run_id INTEGER NOT NULL,
    dataset_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    checksum_sha256 TEXT,
    schema_version TEXT,
    retrieved_at TEXT,
    file_size_bytes INTEGER,
    record_count INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id)
);

CREATE TABLE IF NOT EXISTS ingestion_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingestion_run_id INTEGER NOT NULL,
    source_file_id INTEGER,
    dataset_name TEXT,
    row_number INTEGER,
    issue_code TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'warning',
    message TEXT NOT NULL,
    raw_reference TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id),
    FOREIGN KEY (source_file_id) REFERENCES ingestion_source_files(id)
);
