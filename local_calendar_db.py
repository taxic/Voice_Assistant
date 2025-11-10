"""
Local Calendar Database Manager
Provides fast local access to calendar events with synchronization support for Google Calendar and Outlook.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
import threading
from config_manager import config

class LocalCalendarDB:
    """SQLite database manager for local calendar storage with sync capabilities"""

    def __init__(self, db_path: str = None):
        """Initialize the database connection and create tables"""
        if db_path is None:
            # Get database path from config or use default
            calendar_config = config.get_section('calendar')
            db_path = calendar_config.get('local_db_path', 'calendar_cache.db')

        self.db_path = db_path
        self.lock = threading.Lock()

        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)

        # Initialize database
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Get database connection with proper locking"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
            finally:
                conn.close()

    def _init_database(self):
        """Initialize database tables and indexes"""
        with self.get_connection() as conn:
            # Read and execute schema
            schema_path = os.path.join(os.path.dirname(__file__), 'local_calendar_schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
            else:
                # Fallback schema if file doesn't exist
                self._create_tables_fallback(conn)

            conn.commit()

    def _create_tables_fallback(self, conn: sqlite3.Connection):
        """Fallback table creation if schema file is not available"""
        conn.execute('''
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
            )
        ''')

        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_date ON events(date(start_time))')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_provider ON events(provider)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_sync_status ON events(sync_status)')

    # Event CRUD Operations
    def create_event(self, summary: str, start_time: str, end_time: str,
                    description: str = "", location: str = "", provider: str = "google",
                    google_event_id: str = None, outlook_event_id: str = None) -> int:
        """Create a new event in the local database"""
        now = datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO events (summary, description, location, start_time, end_time,
                                  provider, google_event_id, outlook_event_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (summary, description, location, start_time, end_time, provider,
                  google_event_id, outlook_event_id, now, now))

            event_id = cursor.lastrowid
            conn.commit()
            return event_id

    def get_event(self, event_id: int) -> Optional[Dict]:
        """Get a single event by ID"""
        with self.get_connection() as conn:
            row = conn.execute('SELECT * FROM events WHERE id = ? AND is_deleted = 0', (event_id,)).fetchone()
            return dict(row) if row else None

    def get_event_by_provider_id(self, provider: str, provider_event_id: str) -> Optional[Dict]:
        """Get an event by its provider-specific ID"""
        with self.get_connection() as conn:
            if provider == 'google':
                row = conn.execute('SELECT * FROM events WHERE google_event_id = ? AND is_deleted = 0', (provider_event_id,)).fetchone()
            elif provider == 'outlook':
                row = conn.execute('SELECT * FROM events WHERE outlook_event_id = ? AND is_deleted = 0', (provider_event_id,)).fetchone()
            else:
                return None

            return dict(row) if row else None

    def update_event(self, event_id: int, **kwargs) -> bool:
        """Update an event with the provided fields"""
        if not kwargs:
            return False

        # Add updated_at timestamp
        kwargs['updated_at'] = datetime.now().isoformat()

        # Build dynamic update query
        set_parts = [f"{key} = ?" for key in kwargs.keys()]
        values = list(kwargs.values()) + [event_id]

        with self.get_connection() as conn:
            cursor = conn.execute(f'''
                UPDATE events SET {', '.join(set_parts)}
                WHERE id = ?
            ''', values)

            conn.commit()
            return cursor.rowcount > 0

    def delete_event(self, event_id: int) -> bool:
        """Soft delete an event"""
        return self.update_event(event_id, is_deleted=1, sync_status='pending')

    def find_events_by_summary(self, summary: str, date_obj: datetime = None, limit: int = 10) -> List[Dict]:
        """Find events by summary/title, optionally filtered by date."""
        try:
            with self.get_connection() as conn:
                if date_obj:
                    # Filter by specific date
                    start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0).isoformat()
                    end_of_day = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59).isoformat()

                    rows = conn.execute('''
                        SELECT * FROM events
                        WHERE summary LIKE ? AND start_time >= ? AND start_time <= ?
                        AND is_deleted = 0
                        ORDER BY start_time
                        LIMIT ?
                    ''', (f'%{summary}%', start_of_day, end_of_day, limit)).fetchall()
                else:
                    # Search across all events
                    rows = conn.execute('''
                        SELECT * FROM events
                        WHERE summary LIKE ? AND is_deleted = 0
                        ORDER BY start_time
                        LIMIT ?
                    ''', (f'%{summary}%', limit)).fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            print(f"[ERROR] Failed to find events by summary: {e}")
            return []

    def update_event_by_provider_id(self, provider: str, provider_event_id: str, **kwargs) -> bool:
        """Update an event by its provider-specific ID."""
        try:
            with self.get_connection() as conn:
                if provider == 'google':
                    cursor = conn.execute('''
                        UPDATE events SET updated_at = ?
                        WHERE google_event_id = ? AND is_deleted = 0
                    ''', (datetime.now().isoformat(), provider_event_id))

                    if cursor.rowcount > 0:
                        # Get the event ID and update with new data
                        event = self.get_event_by_provider_id(provider, provider_event_id)
                        if event:
                            return self.update_event(event['id'], **kwargs)

                elif provider == 'outlook':
                    cursor = conn.execute('''
                        UPDATE events SET updated_at = ?
                        WHERE outlook_event_id = ? AND is_deleted = 0
                    ''', (datetime.now().isoformat(), provider_event_id))

                    if cursor.rowcount > 0:
                        # Get the event ID and update with new data
                        event = self.get_event_by_provider_id(provider, provider_event_id)
                        if event:
                            return self.update_event(event['id'], **kwargs)

                return False

        except Exception as e:
            print(f"[ERROR] Failed to update event by provider ID: {e}")
            return False

    def delete_event_by_provider_id(self, provider: str, provider_event_id: str) -> bool:
        """Delete an event by its provider-specific ID."""
        try:
            event = self.get_event_by_provider_id(provider, provider_event_id)
            if event:
                return self.delete_event(event['id'])
            return False
        except Exception as e:
            print(f"[ERROR] Failed to delete event by provider ID: {e}")
            return False

    def get_events_for_date_range(self, start_date: str, end_date: str, provider: str = None) -> List[Dict]:
        """Get all events within a date range"""
        with self.get_connection() as conn:
            if provider:
                rows = conn.execute('''
                    SELECT * FROM events
                    WHERE start_time >= ? AND start_time <= ?
                    AND provider = ? AND is_deleted = 0
                    ORDER BY start_time
                ''', (start_date, end_date, provider)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT * FROM events
                    WHERE start_time >= ? AND start_time <= ?
                    AND is_deleted = 0
                    ORDER BY start_time
                ''', (start_date, end_date)).fetchall()

            return [dict(row) for row in rows]

    def get_events_for_date(self, date_obj) -> List[Dict]:
        """Get all events for a specific date (datetime object)"""
        start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0).isoformat()
        end_of_day = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59).isoformat()

        return self.get_events_for_date_range(start_of_day, end_of_day)

    def find_free_time_slots(self, date_obj, duration_minutes: int, work_start_hour: int = 9, work_end_hour: int = 17) -> List[str]:
        """Find free time slots for a given date and duration"""
        # Get all events for the day
        events = self.get_events_for_date(date_obj)

        # Define work hours
        work_start = datetime(date_obj.year, date_obj.month, date_obj.day, work_start_hour, 0, 0)
        work_end = datetime(date_obj.year, date_obj.month, date_obj.day, work_end_hour, 0, 0)

        # Create list of busy time ranges
        busy_times = []
        for event in events:
            event_start = datetime.fromisoformat(event['start_time'])
            event_end = datetime.fromisoformat(event['end_time'])
            busy_times.append((event_start, event_end))

        # Sort busy times
        busy_times.sort(key=lambda x: x[0])

        # Find free slots
        free_slots = []
        current_time = work_start

        for busy_start, busy_end in busy_times:
            if current_time + timedelta(minutes=duration_minutes) <= busy_start:
                slot_time = current_time.strftime('%H:%M')
                free_slots.append(slot_time)

            current_time = max(current_time, busy_end)

        # Check if there's time after the last event
        if current_time + timedelta(minutes=duration_minutes) <= work_end:
            slot_time = current_time.strftime('%H:%M')
            free_slots.append(slot_time)

        return free_slots

    def find_first_free_slot(self, date_obj, duration_minutes: int) -> Optional[str]:
        """Find the first available time slot for a given duration"""
        slots = self.find_free_time_slots(date_obj, duration_minutes)
        return slots[0] if slots else None

    # Sync-related methods
    def get_pending_sync_events(self, provider: str = None) -> List[Dict]:
        """Get events that need to be synced"""
        with self.get_connection() as conn:
            if provider:
                rows = conn.execute('''
                    SELECT * FROM events
                    WHERE sync_status IN ('pending', 'error')
                    AND provider = ?
                    ORDER BY updated_at
                ''', (provider,)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT * FROM events
                    WHERE sync_status IN ('pending', 'error')
                    ORDER BY updated_at
                ''').fetchall()

            return [dict(row) for row in rows]

    def mark_event_synced(self, event_id: int, sync_time: str = None) -> bool:
        """Mark an event as successfully synced"""
        if sync_time is None:
            sync_time = datetime.now().isoformat()

        return self.update_event(event_id,
                               sync_status='synced',
                               last_sync_at=sync_time)

    def mark_event_sync_error(self, event_id: int, error_message: str) -> bool:
        """Mark an event as having sync error"""
        return self.update_event(event_id,
                               sync_status='error',
                               last_sync_at=datetime.now().isoformat())

    def log_sync_operation(self, provider: str, operation: str, records_affected: int = 0,
                          success: bool = True, error_message: str = None, metadata: dict = None):
        """Log a synchronization operation"""
        with self.get_connection() as conn:
            metadata_json = json.dumps(metadata) if metadata else None

            conn.execute('''
                INSERT INTO sync_log (provider, operation, records_affected, success, error_message, sync_metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (provider, operation, records_affected, 1 if success else 0, error_message, metadata_json))

            conn.commit()

    def get_sync_state(self, provider: str) -> Dict:
        """Get the current sync state for a provider"""
        with self.get_connection() as conn:
            row = conn.execute('SELECT * FROM sync_state WHERE provider = ?', (provider,)).fetchone()
            return dict(row) if row else {}

    def update_sync_state(self, provider: str, **kwargs):
        """Update sync state for a provider"""
        with self.get_connection() as conn:
            # Build dynamic update query
            set_parts = [f"{key} = ?" for key in kwargs.keys()]
            values = list(kwargs.values()) + [provider]

            conn.execute(f'''
                UPDATE sync_state SET {', '.join(set_parts)}
                WHERE provider = ?
            ''', values)

            conn.commit()

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        with self.get_connection() as conn:
            # Get event counts by sync status
            event_stats = conn.execute('''
                SELECT provider, sync_status, COUNT(*) as count
                FROM events
                WHERE is_deleted = 0
                GROUP BY provider, sync_status
            ''').fetchall()

            # Get recent sync operations
            recent_syncs = conn.execute('''
                SELECT provider, operation, success, sync_time, records_affected
                FROM sync_log
                ORDER BY sync_time DESC
                LIMIT 10
            ''').fetchall()

            return {
                'event_stats': [dict(row) for row in event_stats],
                'recent_syncs': [dict(row) for row in recent_syncs]
            }

    def cleanup_old_events(self, days_to_keep: int = 30) -> int:
        """Remove old events that are no longer needed (hard delete)"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        with self.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM events
                WHERE start_time < ? AND is_deleted = 1
            ''', (cutoff_date,))

            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count

    def get_database_size(self) -> Dict[str, int]:
        """Get database size information"""
        with self.get_connection() as conn:
            # Get table counts
            events_count = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
            sync_log_count = conn.execute('SELECT COUNT(*) FROM sync_log').fetchone()[0]

            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

            return {
                'events_count': events_count,
                'sync_log_count': sync_log_count,
                'database_size_bytes': db_size
            }

    def vacuum_database(self):
        """Optimize database by rebuilding and cleaning up space"""
        with self.get_connection() as conn:
            conn.execute('VACUUM')
            conn.commit()

    def export_events(self, start_date: str = None, end_date: str = None, format: str = 'json') -> str:
        """Export events to JSON or CSV format"""
        with self.get_connection() as conn:
            if start_date and end_date:
                rows = conn.execute('''
                    SELECT * FROM events
                    WHERE start_time >= ? AND start_time <= ? AND is_deleted = 0
                    ORDER BY start_time
                ''', (start_date, end_date)).fetchall()
            else:
                rows = conn.execute('SELECT * FROM events WHERE is_deleted = 0 ORDER BY start_time').fetchall()

            events = [dict(row) for row in rows]

            if format.lower() == 'json':
                return json.dumps(events, indent=2, default=str)
            else:
                # Simple CSV format
                if not events:
                    return ""

                import csv
                import io

                output = io.StringIO()
                fieldnames = events[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(events)

                return output.getvalue()

    def import_events(self, data: str, format: str = 'json', source_provider: str = 'import') -> int:
        """Import events from JSON or CSV data"""
        imported_count = 0

        try:
            if format.lower() == 'json':
                events = json.loads(data)
            else:
                # Parse CSV
                import csv
                import io
                reader = csv.DictReader(io.StringIO(data))
                events = list(reader)

            # Convert string dates back to datetime objects for processing
            for event in events:
                if isinstance(event.get('start_time'), str):
                    # Ensure proper datetime format
                    try:
                        datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                    except ValueError:
                        continue  # Skip invalid dates

                # Set provider if not specified
                if 'provider' not in event:
                    event['provider'] = source_provider

                # Create the event
                self.create_event(
                    summary=event.get('summary', ''),
                    start_time=event['start_time'],
                    end_time=event.get('end_time', ''),
                    description=event.get('description', ''),
                    location=event.get('location', ''),
                    provider=event.get('provider', source_provider),
                    google_event_id=event.get('google_event_id'),
                    outlook_event_id=event.get('outlook_event_id')
                )
                imported_count += 1

        except Exception as e:
            print(f"[ERROR] Failed to import events: {e}")

        return imported_count