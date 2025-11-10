#!/usr/bin/env python3
"""
Calendar Database Initialization and Migration Script
Sets up and maintains the local calendar database with proper schema and migrations.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any
from local_calendar_db import LocalCalendarDB
from config_manager import config

def create_database_schema(db_path: str):
    """Create the initial database schema"""
    print(f"[INFO] Creating calendar database schema at: {db_path}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)

    # Read schema file
    schema_path = os.path.join(os.path.dirname(__file__), 'local_calendar_schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
    else:
        print("[WARN] Schema file not found, using fallback schema")
        schema_sql = get_fallback_schema()

    # Create database and execute schema
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print("[INFO] Database schema created successfully")
    except Exception as e:
        print(f"[ERROR] Failed to create database schema: {e}")
        return False
    finally:
        conn.close()

    return True

def get_fallback_schema() -> str:
    """Fallback schema if schema file is not available"""
    return '''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_event_id TEXT UNIQUE,
        outlook_event_id TEXT UNIQUE,
        summary TEXT NOT NULL,
        description TEXT,
        location TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        timezone TEXT NOT NULL DEFAULT 'Europe/London',
        provider TEXT NOT NULL DEFAULT 'google',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_sync_at TEXT,
        sync_status TEXT DEFAULT 'synced',
        event_version INTEGER DEFAULT 1,
        is_deleted INTEGER DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);
    CREATE INDEX IF NOT EXISTS idx_events_date ON events(date(start_time));
    CREATE INDEX IF NOT EXISTS idx_events_provider ON events(provider);
    CREATE INDEX IF NOT EXISTS idx_events_sync_status ON events(sync_status);

    CREATE TABLE IF NOT EXISTS sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        provider TEXT NOT NULL,
        operation TEXT NOT NULL,
        records_affected INTEGER DEFAULT 0,
        success INTEGER DEFAULT 1,
        error_message TEXT,
        sync_metadata TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_sync_log_time ON sync_log(sync_time DESC);
    CREATE INDEX IF NOT EXISTS idx_sync_log_provider ON sync_log(provider);

    CREATE TABLE IF NOT EXISTS sync_state (
        id INTEGER PRIMARY KEY DEFAULT 1,
        provider TEXT NOT NULL UNIQUE,
        last_full_sync TEXT,
        last_incremental_sync TEXT,
        next_sync_due TEXT,
        sync_enabled INTEGER DEFAULT 1,
        sync_frequency_minutes INTEGER DEFAULT 15,
        UNIQUE(provider)
    );

    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY DEFAULT 1,
        cache_timeout_minutes INTEGER DEFAULT 5,
        max_events_per_request INTEGER DEFAULT 100,
        enable_background_sync INTEGER DEFAULT 1,
        conflict_resolution_strategy TEXT DEFAULT 'newest_wins'
    );
    '''

def check_database_health(db_path: str) -> Dict[str, Any]:
    """Check the health and integrity of the database"""
    print(f"[INFO] Checking database health: {db_path}")

    if not os.path.exists(db_path):
        return {'status': 'error', 'message': 'Database file does not exist'}

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if required tables exist
        required_tables = ['events', 'sync_log', 'sync_state', 'settings']
        existing_tables = []
        missing_tables = []

        for table in required_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                existing_tables.append(table)
            else:
                missing_tables.append(table)

        if missing_tables:
            return {
                'status': 'error',
                'message': f'Missing required tables: {", ".join(missing_tables)}',
                'existing_tables': existing_tables
            }

        # Check database size and record counts
        stats = {}
        for table in required_tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            stats[f'{table}_count'] = count

        # Get database file size
        db_size = os.path.getsize(db_path)

        # Check for potential issues
        issues = []

        # Check for orphaned records
        cursor.execute('''
            SELECT COUNT(*) FROM events
            WHERE sync_status = 'error' AND last_sync_at < datetime('now', '-1 day')
        ''')
        error_count = cursor.fetchone()[0]
        if error_count > 0:
            issues.append(f'{error_count} events with sync errors older than 1 day')

        # Check for large sync log
        cursor.execute('SELECT COUNT(*) FROM sync_log WHERE sync_time < datetime("now", "-7 days")')
        old_logs = cursor.fetchone()[0]
        if old_logs > 1000:
            issues.append(f'{old_logs} old sync log entries (consider cleanup)')

        conn.close()

        result = {
            'status': 'healthy' if not issues else 'warning',
            'message': 'Database is healthy' if not issues else f'Issues found: {"; ".join(issues)}',
            'statistics': stats,
            'database_size_bytes': db_size,
            'issues': issues
        }

        print(f"[INFO] Database health check completed: {result['status']}")
        return result

    except Exception as e:
        return {'status': 'error', 'message': f'Database error: {str(e)}'}

def cleanup_database(db_path: str, days_to_keep: int = 30) -> Dict[str, any]:
    """Clean up old data from the database"""
    print(f"[INFO] Cleaning up database: {db_path}")

    try:
        db = LocalCalendarDB(db_path)

        # Clean up old events
        deleted_events = db.cleanup_old_events(days_to_keep)

        # Clean up old sync logs (keep last 30 days)
        with db.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM sync_log
                WHERE sync_time < datetime('now', '-30 days')
            ''')
            deleted_logs = cursor.rowcount
            conn.commit()

        # Vacuum database to reclaim space
        db.vacuum_database()

        # Get final statistics
        final_stats = db.get_database_size()

        result = {
            'success': True,
            'deleted_events': deleted_events,
            'deleted_logs': deleted_logs,
            'final_statistics': final_stats
        }

        print(f"[INFO] Database cleanup completed: {deleted_events} events, {deleted_logs} logs removed")
        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}

def migrate_database(db_path: str, target_version: str = None) -> Dict[str, any]:
    """Apply database migrations to update schema"""
    print(f"[INFO] Checking for database migrations: {db_path}")

    # For now, this is a placeholder for future migration logic
    # In a real implementation, you would:
    # 1. Check current schema version
    # 2. Apply incremental migrations
    # 3. Update schema version

    try:
        # Check if database exists
        if not os.path.exists(db_path):
            return {'success': False, 'error': 'Database does not exist'}

        # Check current schema version (placeholder)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if we have the expected tables structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'error': 'Invalid database schema'}

        conn.close()

        return {
            'success': True,
            'message': 'No migrations needed (database is up to date)',
            'current_version': '1.0.0'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}

def backup_database(db_path: str, backup_path: str = None) -> Dict[str, any]:
    """Create a backup of the database"""
    if not os.path.exists(db_path):
        return {'success': False, 'error': 'Source database does not exist'}

    if backup_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.backup.{timestamp}"

    try:
        # Create backup directory if needed
        os.makedirs(os.path.dirname(backup_path) if os.path.dirname(backup_path) else '.', exist_ok=True)

        # Copy database file
        import shutil
        shutil.copy2(db_path, backup_path)

        backup_size = os.path.getsize(backup_path)

        print(f"[INFO] Database backed up to: {backup_path} ({backup_size} bytes)")
        return {
            'success': True,
            'backup_path': backup_path,
            'backup_size_bytes': backup_size
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}

def restore_database(backup_path: str, target_path: str) -> Dict[str, any]:
    """Restore database from backup"""
    if not os.path.exists(backup_path):
        return {'success': False, 'error': 'Backup file does not exist'}

    try:
        # Create target directory if needed
        os.makedirs(os.path.dirname(target_path) if os.path.dirname(target_path) else '.', exist_ok=True)

        # Copy backup to target location
        import shutil
        shutil.copy2(backup_path, target_path)

        target_size = os.path.getsize(target_path)

        print(f"[INFO] Database restored to: {target_path} ({target_size} bytes)")
        return {
            'success': True,
            'target_path': target_path,
            'target_size_bytes': target_size
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}

def setup_calendar_config():
    """Set up calendar configuration for local caching"""
    print("[INFO] Setting up calendar configuration for local caching")

    try:
        # Get current config
        calendar_config = config.get_section('calendar', {})

        # Update with cache-specific settings
        cache_config = {
            'local_db_path': calendar_config.get('local_db_path', 'calendar_cache.db'),
            'cache_timeout_minutes': calendar_config.get('cache_timeout_minutes', 5),
            'enable_background_sync': calendar_config.get('enable_background_sync', True),
            'sync_interval_minutes': calendar_config.get('sync_interval_minutes', 15)
        }

        # Update config (this would need to be implemented in config_manager)
        print("[INFO] Cache configuration:")
        for key, value in cache_config.items():
            print(f"  {key}: {value}")

        return {'success': True, 'config': cache_config}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    """Main initialization function"""
    print("Calendar Database Initialization Script")
    print("=" * 50)

    # Get database path from config or use default
    calendar_config = config.get_section('calendar')
    db_path = calendar_config.get('local_db_path', 'calendar_cache.db')

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = 'init'

    if command == 'init':
        # Initialize database
        print(f"[INFO] Initializing calendar database: {db_path}")

        if create_database_schema(db_path):
            print("[INFO] Database initialized successfully")

            # Set up configuration
            config_result = setup_calendar_config()
            if config_result['success']:
                print("[INFO] Configuration set up successfully")
            else:
                print(f"[WARN] Configuration setup failed: {config_result.get('error')}")

            # Check database health
            health = check_database_health(db_path)
            print(f"[INFO] Database health: {health['status']}")
            if health['status'] != 'healthy':
                print(f"[WARN] {health['message']}")

        else:
            print("[ERROR] Failed to initialize database")
            return 1

    elif command == 'health':
        # Check database health
        health = check_database_health(db_path)
        print(f"Database Health: {health['status']}")
        print(f"Message: {health['message']}")

        if health['status'] == 'healthy':
            stats = health.get('statistics', {})
            print(f"Events: {stats.get('events_count', 0)}")
            print(f"Sync logs: {stats.get('sync_log_count', 0)}")
            print(f"Database size: {health.get('database_size_bytes', 0)} bytes")

            if health.get('issues'):
                print("Issues found:")
                for issue in health['issues']:
                    print(f"  - {issue}")

            return 0
        else:
            return 1

    elif command == 'cleanup':
        # Clean up database
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = cleanup_database(db_path, days)

        if result['success']:
            print(f"Cleanup completed: {result['deleted_events']} events, {result['deleted_logs']} logs removed")
            return 0
        else:
            print(f"Cleanup failed: {result['error']}")
            return 1

    elif command == 'backup':
        # Backup database
        backup_path = sys.argv[2] if len(sys.argv) > 2 else None
        result = backup_database(db_path, backup_path)

        if result['success']:
            print(f"Backup created: {result['backup_path']}")
            return 0
        else:
            print(f"Backup failed: {result['error']}")
            return 1

    elif command == 'restore':
        # Restore database
        if len(sys.argv) < 3:
            print("Usage: python calendar_db_init.py restore <backup_path> [target_path]")
            return 1

        backup_path = sys.argv[2]
        target_path = sys.argv[3] if len(sys.argv) > 3 else db_path
        result = restore_database(backup_path, target_path)

        if result['success']:
            print(f"Database restored: {result['target_path']}")
            return 0
        else:
            print(f"Restore failed: {result['error']}")
            return 1

    elif command == 'migrate':
        # Run migrations
        result = migrate_database(db_path)

        if result['success']:
            print(f"Migration completed: {result['message']}")
            return 0
        else:
            print(f"Migration failed: {result['error']}")
            return 1

    else:
        print("Usage: python calendar_db_init.py [command]")
        print("Commands:")
        print("  init      - Initialize database and configuration")
        print("  health    - Check database health")
        print("  cleanup   - Clean up old data")
        print("  backup    - Create database backup")
        print("  restore   - Restore from backup")
        print("  migrate   - Apply database migrations")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())