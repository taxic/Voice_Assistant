-- Local Calendar Database Schema
-- This schema provides fast local access to calendar events while maintaining sync with Google Calendar

-- Events table - stores all calendar events locally
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_event_id TEXT UNIQUE,           -- Google Calendar event ID (nullable for non-Google events)
    outlook_event_id TEXT UNIQUE,          -- Outlook event ID (nullable for non-Outlook events)
    summary TEXT NOT NULL,                 -- Event title/summary
    description TEXT,                      -- Event description
    location TEXT,                         -- Event location
    start_time TEXT NOT NULL,              -- ISO format datetime string
    end_time TEXT NOT NULL,                -- ISO format datetime string
    timezone TEXT NOT NULL DEFAULT 'Europe/London',
    provider TEXT NOT NULL DEFAULT 'google', -- 'google', 'outlook', or 'both'
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TEXT,                     -- When this event was last synced with the provider
    sync_status TEXT DEFAULT 'synced',     -- 'pending', 'synced', 'error', 'deleted'
    event_version INTEGER DEFAULT 1,       -- For conflict resolution during sync
    is_deleted INTEGER DEFAULT 0,          -- Soft delete flag
    UNIQUE(google_event_id),
    UNIQUE(outlook_event_id)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);
CREATE INDEX IF NOT EXISTS idx_events_end_time ON events(end_time);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date(start_time));
CREATE INDEX IF NOT EXISTS idx_events_provider ON events(provider);
CREATE INDEX IF NOT EXISTS idx_events_sync_status ON events(sync_status);
CREATE INDEX IF NOT EXISTS idx_events_google_id ON events(google_event_id);
CREATE INDEX IF NOT EXISTS idx_events_outlook_id ON events(outlook_event_id);

-- Sync log table - tracks synchronization operations
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    provider TEXT NOT NULL,                -- 'google', 'outlook'
    operation TEXT NOT NULL,               -- 'full_sync', 'incremental_sync', 'create', 'update', 'delete'
    records_affected INTEGER DEFAULT 0,
    success INTEGER DEFAULT 1,             -- 0 for failure, 1 for success
    error_message TEXT,
    sync_metadata TEXT                     -- JSON string for additional sync info
);

-- Index for sync log
CREATE INDEX IF NOT EXISTS idx_sync_log_time ON sync_log(sync_time DESC);
CREATE INDEX IF NOT EXISTS idx_sync_log_provider ON sync_log(provider);

-- Sync state table - tracks last sync times and status
CREATE TABLE IF NOT EXISTS sync_state (
    id INTEGER PRIMARY KEY DEFAULT 1,
    provider TEXT NOT NULL UNIQUE,
    last_full_sync TEXT,                   -- When we last did a full sync
    last_incremental_sync TEXT,            -- When we last did an incremental sync
    next_sync_due TEXT,                    -- When next sync should happen
    sync_enabled INTEGER DEFAULT 1,        -- Whether sync is enabled for this provider
    sync_frequency_minutes INTEGER DEFAULT 15, -- How often to sync (minutes)
    UNIQUE(provider)
);

-- Insert default sync state for Google Calendar
INSERT OR IGNORE INTO sync_state (provider, sync_enabled, sync_frequency_minutes)
VALUES ('google', 1, 15);

-- Settings table - for database configuration
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    cache_timeout_minutes INTEGER DEFAULT 5, -- How long to cache API responses
    max_events_per_request INTEGER DEFAULT 100, -- Max events to fetch per API call
    enable_background_sync INTEGER DEFAULT 1,   -- Whether to enable background sync
    conflict_resolution_strategy TEXT DEFAULT 'newest_wins' -- 'newest_wins', 'local_wins', 'remote_wins'
);

-- Insert default settings
INSERT OR IGNORE INTO settings (id) VALUES (1);

-- Views for common queries
CREATE VIEW IF NOT EXISTS events_today AS
SELECT * FROM events
WHERE date(start_time) = date('now', 'localtime')
AND is_deleted = 0
ORDER BY start_time;

CREATE VIEW IF NOT EXISTS events_this_week AS
SELECT * FROM events
WHERE start_time >= date('now', 'localtime', 'weekday 0', '-0 days')
AND start_time < date('now', 'localtime', 'weekday 0', '+7 days')
AND is_deleted = 0
ORDER BY start_time;

CREATE VIEW IF NOT EXISTS pending_sync_events AS
SELECT * FROM events
WHERE sync_status IN ('pending', 'error')
ORDER BY updated_at;

CREATE VIEW IF NOT EXISTS events_by_provider AS
SELECT
    provider,
    COUNT(*) as total_events,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_events,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_events,
    COUNT(CASE WHEN sync_status = 'error' THEN 1 END) as error_events,
    MAX(last_sync_at) as last_sync_time
FROM events
WHERE is_deleted = 0
GROUP BY provider;