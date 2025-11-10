"""
Calendar Caching and Synchronization Manager
Provides intelligent caching with background synchronization for improved performance.
"""

import threading
import time
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import json
import pytz
from local_calendar_db import LocalCalendarDB
from config_manager import config

class CalendarCacheSync:
    """Manages local caching and synchronization with Google Calendar"""

    def __init__(self, db_path: str = None, sync_interval_minutes: int = 15, google_calendar = None):
        """Initialize the cache sync manager"""
        self.local_db = LocalCalendarDB(db_path)
        self.google_calendar = google_calendar  # Accept GoogleCalendar instance to avoid circular import
        self.sync_interval_minutes = sync_interval_minutes

        # Sync control
        self.sync_enabled = True
        self.sync_thread = None
        self.last_full_sync = None
        self.last_incremental_sync = None

        # Initialize last sync times from database
        try:
            sync_state = self.local_db.get_sync_state('google')
            last_full_str = sync_state.get('last_full_sync')
            last_incremental_str = sync_state.get('last_incremental_sync')

            # Convert string timestamps to datetime objects
            if last_full_str:
                try:
                    # Handle different datetime string formats
                    if last_full_str.endswith('Z'):
                        dt_str = last_full_str.replace('Z', '+00:00')
                    else:
                        dt_str = last_full_str

                    # Parse as naive datetime first, then make timezone aware
                    try:
                        if '+' in dt_str or 'T' in dt_str:
                            # Has timezone info, parse directly
                            dt = datetime.fromisoformat(dt_str)
                        else:
                            # Naive datetime, make it UTC
                            dt = datetime.fromisoformat(dt_str).replace(tzinfo=pytz.UTC)
                    except Exception as e:
                        if "naive" in str(e) or "tzinfo" in str(e):
                            # Already has timezone info, use as-is
                            dt = datetime.fromisoformat(dt_str)
                        else:
                            raise

                    self.last_full_sync = dt
                except (ValueError, TypeError):
                    self.last_full_sync = None

            if last_incremental_str:
                try:
                    # Handle different datetime string formats
                    if last_incremental_str.endswith('Z'):
                        dt_str = last_incremental_str.replace('Z', '+00:00')
                    else:
                        dt_str = last_incremental_str

                    # Parse as naive datetime first, then make timezone aware
                    try:
                        if '+' in dt_str or 'T' in dt_str:
                            # Has timezone info, parse directly
                            dt = datetime.fromisoformat(dt_str)
                        else:
                            # Naive datetime, make it UTC
                            dt = datetime.fromisoformat(dt_str).replace(tzinfo=pytz.UTC)
                    except Exception as e:
                        if "naive" in str(e) or "tzinfo" in str(e):
                            # Already has timezone info, use as-is
                            dt = datetime.fromisoformat(dt_str)
                        else:
                            raise

                    self.last_incremental_sync = dt
                except (ValueError, TypeError):
                    self.last_incremental_sync = None
        except Exception:
            # If database query fails, leave as None
            pass

        # Get configuration
        calendar_config = config.get_section('calendar')
        self.cache_timeout_minutes = calendar_config.get('cache_timeout_minutes', 5)
        self.enable_background_sync = calendar_config.get('enable_background_sync', True)

        # Start background sync if enabled
        if self.enable_background_sync:
            self.start_background_sync()

    def start_background_sync(self):
        """Start the background synchronization thread"""
        if self.sync_thread and self.sync_thread.is_alive():
            return  # Already running

        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        print(f"[INFO] Background calendar sync started (interval: {self.sync_interval_minutes} minutes)")

    def stop_background_sync(self):
        """Stop the background synchronization thread"""
        self.sync_enabled = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("[INFO] Background calendar sync stopped")

    def _sync_worker(self):
        """Background worker that performs periodic synchronization"""
        while self.sync_enabled:
            try:
                # Perform full sync (skip incremental for now due to datetime issues)
                self.perform_full_sync()
                self.last_full_sync = datetime.now()

                # Update incremental sync time for compatibility
                self.last_incremental_sync = datetime.now()

            except Exception as e:
                print(f"[ERROR] Background sync failed: {e}")
                self.local_db.log_sync_operation(
                    provider='google',
                    operation='background_sync',
                    success=False,
                    error_message=str(e)
                )

            # Wait for next sync interval
            time.sleep(self.sync_interval_minutes * 60)

    def perform_full_sync(self) -> Dict[str, Any]:
        """Perform a full synchronization with Google Calendar"""
        print("[INFO] Starting full calendar sync...")

        if not self.google_calendar or not self.google_calendar.service:
            return {'success': False, 'error': 'Google Calendar not available'}

        try:
            # Get all events from Google Calendar for the next 30 days
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)

            # Convert to Google Calendar API format
            tz = pytz.timezone(config.get('calendar.timezone', 'Europe/London'))
            start_datetime = tz.localize(datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0))
            end_datetime = tz.localize(datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59))

            # Fetch events from Google Calendar
            events_result = self.google_calendar.service.events().list(
                calendarId='primary',
                timeMin=start_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            google_events = events_result.get('items', [])

            # Process and store events locally
            synced_count = 0
            for google_event in google_events:
                self._sync_google_event_to_local(google_event)
                synced_count += 1

            # Mark old local events as deleted if not in Google Calendar
            self._cleanup_missing_events(start_datetime, end_datetime)

            # Update sync state and instance variables
            current_time = datetime.now()
            self.local_db.update_sync_state('google',
                last_full_sync=current_time.isoformat(),
                next_sync_due=current_time.isoformat()
            )
            self.last_full_sync = current_time

            # Log success
            self.local_db.log_sync_operation(
                provider='google',
                operation='full_sync',
                records_affected=synced_count,
                success=True
            )

            print(f"[INFO] Full sync completed: {synced_count} events synchronized")
            return {'success': True, 'events_synced': synced_count}

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Full sync failed: {error_msg}")

            self.local_db.log_sync_operation(
                provider='google',
                operation='full_sync',
                success=False,
                error_message=error_msg
            )

            return {'success': False, 'error': error_msg}

    def perform_incremental_sync(self) -> Dict[str, Any]:
        """Perform an incremental synchronization (only changes since last sync)"""
        print("[INFO] Starting incremental calendar sync...")

        if not self.google_calendar or not self.google_calendar.service:
            return {'success': False, 'error': 'Google Calendar not available'}

        try:
            # Wrap the entire sync in a try-catch to handle datetime issues gracefully
            return self._perform_incremental_sync_safe()
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Incremental sync failed: {error_msg}")

            self.local_db.log_sync_operation(
                provider='google',
                operation='incremental_sync',
                success=False,
                error_message=error_msg
            )

            return {'success': False, 'error': error_msg}

    def _perform_incremental_sync_safe(self) -> Dict[str, Any]:
        """Internal method for incremental sync with better error handling"""
        # Get the last sync time
        sync_state = self.local_db.get_sync_state('google')
        last_sync = sync_state.get('last_incremental_sync') or sync_state.get('last_full_sync')

        if not last_sync:
            # No previous sync, do full sync instead
            return self.perform_full_sync()

        try:
            if last_sync is None:
                return self.perform_full_sync()

            # Parse datetime string safely
            if isinstance(last_sync, str):
                if last_sync.endswith('Z'):
                    last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                else:
                    last_sync_dt = datetime.fromisoformat(last_sync)
            else:
                return self.perform_full_sync()  # Invalid format, do full sync

            # Ensure timezone awareness
            if last_sync_dt.tzinfo is None:
                last_sync_dt = last_sync_dt.replace(tzinfo=pytz.UTC)
        except (ValueError, TypeError, AttributeError):
            # Invalid date format, do full sync instead
            return self.perform_full_sync()

        # Get events modified since last sync
        tz = pytz.timezone(config.get('calendar.timezone', 'Europe/London'))
        start_datetime = tz.localize(last_sync_dt.replace(hour=0, minute=0, second=0, microsecond=0))
        end_datetime = tz.localize(datetime.now() + timedelta(days=7))  # Look ahead 7 days

        events_result = self.google_calendar.service.events().list(
            calendarId='primary',
            timeMin=start_datetime.isoformat(),
            timeMax=end_datetime.isoformat(),
            singleEvents=True,
            orderBy='updated'
        ).execute()

        google_events = events_result.get('items', [])

        # Process updated events
        synced_count = 0
        for google_event in google_events:
            try:
                updated_str = google_event['updated'].replace('Z', '+00:00')
                updated_dt = datetime.fromisoformat(updated_str)

                # Ensure both datetimes are timezone-aware for comparison
                try:
                    if updated_dt.tzinfo is None:
                        updated_dt = updated_dt.replace(tzinfo=pytz.UTC)
                except Exception as e:
                    error_msg = str(e)
                    if "tzinfo" in error_msg or "naive" in error_msg:
                        pass  # Already has timezone info
                    else:
                        print(f"[WARN] Unexpected datetime error for updated_dt: {error_msg}")

                try:
                    if last_sync_dt.tzinfo is None:
                        last_sync_dt = last_sync_dt.replace(tzinfo=pytz.UTC)
                except Exception as e:
                    error_msg = str(e)
                    if "tzinfo" in error_msg or "naive" in error_msg:
                        pass  # Already has timezone info
                    else:
                        print(f"[WARN] Unexpected datetime error for last_sync_dt: {error_msg}")

                # Convert to same timezone for comparison
                if updated_dt.tzinfo != last_sync_dt.tzinfo:
                    updated_dt = updated_dt.astimezone(last_sync_dt.tzinfo)

                if updated_dt > last_sync_dt:
                    self._sync_google_event_to_local(google_event)
                    synced_count += 1
            except (ValueError, KeyError, TypeError) as e:
                print(f"[WARN] Skipping event due to datetime parsing error: {e}")
                continue

        # Update sync state and instance variables
        current_time = datetime.now()
        self.local_db.update_sync_state('google',
            last_incremental_sync=current_time.isoformat()
        )
        self.last_incremental_sync = current_time

        # Log success
        self.local_db.log_sync_operation(
            provider='google',
            operation='incremental_sync',
            records_affected=synced_count,
            success=True
        )

        print(f"[INFO] Incremental sync completed: {synced_count} events synchronized")
        return {'success': True, 'events_synced': synced_count}

    def _sync_google_event_to_local(self, google_event: Dict):
        """Sync a single Google Calendar event to local database"""
        try:
            # Extract event details
            google_event_id = google_event.get('id')
            if not google_event_id:
                return  # Skip events without ID

            # Check if event already exists locally
            existing_event = self.local_db.get_event_by_provider_id('google', google_event_id)

            # Extract datetime information
            start_info = google_event.get('start', {})
            end_info = google_event.get('end', {})

            if 'dateTime' in start_info:
                start_time_str = start_info['dateTime']
                end_time_str = end_info['dateTime']

                # Parse and normalize datetime
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))

                # Convert to ISO format string for storage
                start_time = start_time.isoformat()
                end_time = end_time.isoformat()
            else:
                # All-day event
                start_time = start_info['date'] + 'T00:00:00'
                end_time = end_info['date'] + 'T23:59:59'

            # Prepare event data (only include parameters that create_event accepts)
            if existing_event:
                # Update existing event
                event_data = {
                    'summary': google_event.get('summary', 'Untitled Event'),
                    'description': google_event.get('description', ''),
                    'location': google_event.get('location', ''),
                    'start_time': start_time,
                    'end_time': end_time,
                    'provider': 'google',
                    'google_event_id': google_event_id,
                    'sync_status': 'synced',
                    'last_sync_at': datetime.now().isoformat(),
                    'event_version': existing_event.get('event_version', 1) + 1
                }
                self.local_db.update_event(existing_event['id'], **event_data)
            else:
                # Create new event (only pass parameters that create_event accepts)
                try:
                    event_id = self.local_db.create_event(
                        summary=google_event.get('summary', 'Untitled Event'),
                        start_time=start_time,
                        end_time=end_time,
                        description=google_event.get('description', ''),
                        location=google_event.get('location', ''),
                        provider='google',
                        google_event_id=google_event_id
                    )

                    # Mark as synced after creation
                    self.local_db.mark_event_synced(event_id)
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        # Event already exists, try to get it and update it
                        existing_event_retry = self.local_db.get_event_by_provider_id('google', google_event_id)
                        if existing_event_retry:
                            print(f"[INFO] Event {google_event_id} already exists, updating instead")
                            event_data = {
                                'summary': google_event.get('summary', 'Untitled Event'),
                                'description': google_event.get('description', ''),
                                'location': google_event.get('location', ''),
                                'start_time': start_time,
                                'end_time': end_time,
                                'provider': 'google',
                                'google_event_id': google_event_id,
                                'sync_status': 'synced',
                                'last_sync_at': datetime.now().isoformat(),
                                'event_version': existing_event_retry.get('event_version', 1) + 1
                            }
                            self.local_db.update_event(existing_event_retry['id'], **event_data)
                        else:
                            print(f"[WARN] Could not find existing event {google_event_id} to update")
                    else:
                        raise

        except Exception as e:
            print(f"[ERROR] Failed to sync Google event {google_event.get('id', 'unknown')}: {e}")

    def _cleanup_missing_events(self, start_datetime: datetime, end_datetime: datetime):
        """Mark local events as deleted if they're no longer in Google Calendar"""
        if not self.google_calendar or not self.google_calendar.service:
            return  # Skip cleanup if Google Calendar not available

        try:
            # Get all Google events for the time range
            events_result = self.google_calendar.service.events().list(
                calendarId='primary',
                timeMin=start_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                singleEvents=True
            ).execute()

            google_events = events_result.get('items', [])
            google_event_ids = {event['id'] for event in google_events if event.get('id')}

            # Find local Google events that are no longer in Google Calendar
            local_events = self.local_db.get_events_for_date_range(
                start_datetime.isoformat(),
                end_datetime.isoformat(),
                provider='google'
            )

            deleted_count = 0
            for local_event in local_events:
                if local_event['google_event_id'] not in google_event_ids:
                    # Mark as deleted
                    self.local_db.update_event(
                        local_event['id'],
                        is_deleted=1,
                        sync_status='pending'
                    )
                    deleted_count += 1

            if deleted_count > 0:
                print(f"[INFO] Marked {deleted_count} events as deleted (no longer in Google Calendar)")

        except Exception as e:
            print(f"[ERROR] Failed to cleanup missing events: {e}")

    # Cached read operations (fast local access)
    def get_events_for_date(self, date_obj) -> str:
        """Get events for a date from local cache (fast)"""
        try:
            # Get events from local database
            events = self.local_db.get_events_for_date(date_obj)

            if not events:
                # No events in cache, try to sync first
                if self._should_refresh_cache():
                    self.perform_incremental_sync()

                    # Try again after sync
                    events = self.local_db.get_events_for_date(date_obj)

                if not events:
                    if date_obj.strftime('%A') == datetime.now().strftime('%A'):
                        return "You have no events today."
                    else:
                        return f"You have no events on {date_obj.strftime('%A')}."

            # Format response
            response_lines = [f"Here are your events on {date_obj.strftime('%A')}:"]

            for event in events:
                start = event['start_time']
                start_time = datetime.fromisoformat(start).strftime('%H:%M') if 'T' in start else "All-day"
                summary = event['summary']
                response_lines.append(f"• {summary} at {start_time}")

            return "\n".join(response_lines)

        except Exception as e:
            print(f"[ERROR] Failed to get cached events for date: {e}")
            return f"Sorry, I encountered an error retrieving events: {str(e)}"

    def find_free_time_slot(self, duration_minutes: int, date_obj) -> Optional[str]:
        """Find free time slot using local cache"""
        try:
            # Check cache first
            if self._should_refresh_cache():
                self.perform_incremental_sync()

            return self.local_db.find_first_free_slot(date_obj, duration_minutes)

        except Exception as e:
            print(f"[ERROR] Failed to find free time slot: {e}")
            return None

    def _should_refresh_cache(self) -> bool:
        """Determine if cache should be refreshed based on timeout"""
        try:
            sync_state = self.local_db.get_sync_state('google')
            last_sync = sync_state.get('last_incremental_sync') or sync_state.get('last_full_sync')

            if not last_sync:
                return True  # No previous sync, should refresh

            try:
                # Parse datetime string safely
                if isinstance(last_sync, str):
                    if last_sync.endswith('Z'):
                        last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                    else:
                        last_sync_dt = datetime.fromisoformat(last_sync)
                else:
                    return True  # Invalid format, refresh needed

                # Ensure timezone awareness for comparison
                try:
                    if last_sync_dt.tzinfo is None:
                        last_sync_dt = last_sync_dt.replace(tzinfo=pytz.UTC)
                except Exception as e:
                    error_msg = str(e)
                    if "tzinfo" in error_msg or "naive" in error_msg:
                        # Already has timezone info, use as-is
                        pass
                    else:
                        print(f"[WARN] Unexpected datetime error in _should_refresh_cache: {error_msg}")
                        return True  # On error, assume refresh is needed

                current_dt = datetime.now().replace(tzinfo=pytz.UTC)
                time_since_sync = current_dt - last_sync_dt

                return time_since_sync.total_seconds() > (self.cache_timeout_minutes * 60)
            except (ValueError, TypeError, AttributeError):
                return True  # On date parsing error, assume refresh is needed

        except Exception:
            return True  # On error, assume refresh is needed

    # Write operations (write-through to both local and Google)
    def create_event(self, summary: str, start_time: str, end_time: str,
                    description: str = "", location: str = "") -> str:
        """Create event in both local database and Google Calendar"""
        try:
            # Create in Google Calendar first (if available)
            if self.google_calendar and self.google_calendar.service:
                google_result = self.google_calendar.create_event(summary, start_time, end_time)
                # Extract Google event ID from result if possible
                google_event_id = None
                # Note: In a real implementation, you'd parse the Google response to get the event ID
            else:
                google_result = f"Event '{summary}' created locally (Google Calendar not available)"
                google_event_id = None

            # Create in local database
            event_id = self.local_db.create_event(
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                provider='google',
                google_event_id=google_event_id
            )

            # Mark as synced
            self.local_db.mark_event_synced(event_id)

            return google_result

        except Exception as e:
            print(f"[ERROR] Failed to create event: {e}")
            return f"Sorry, I encountered an error creating the event: {str(e)}"

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        try:
            sync_state = self.local_db.get_sync_state('google')
            stats = self.local_db.get_sync_stats()
            db_size = self.local_db.get_database_size()

            return {
                'sync_enabled': self.sync_enabled,
                'last_full_sync': sync_state.get('last_full_sync'),
                'last_incremental_sync': sync_state.get('last_incremental_sync'),
                'next_sync_due': sync_state.get('next_sync_due'),
                'sync_stats': stats,
                'database_info': db_size,
                'cache_timeout_minutes': self.cache_timeout_minutes
            }

        except Exception as e:
            return {'error': str(e)}

    def force_refresh_cache(self) -> Dict[str, Any]:
        """Force a full refresh of the cache"""
        return self.perform_full_sync()

    def cleanup_cache(self, days_to_keep: int = 30) -> int:
        """Clean up old events from cache"""
        return self.local_db.cleanup_old_events(days_to_keep)

    def export_cache(self, format: str = 'json') -> str:
        """Export cached events"""
        return self.local_db.export_events(format=format)

    def import_cache(self, data: str, format: str = 'json') -> int:
        """Import events into cache"""
        return self.local_db.import_events(data, format, 'import')

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return self.local_db.get_database_size()