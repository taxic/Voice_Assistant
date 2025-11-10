from __future__ import print_function
from datetime import datetime, timedelta
import os.path
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
import pytz
from typing import Optional, Dict
from config_manager import config
from calendar_cache_sync import CalendarCacheSync

class GoogleCalendar:
    def __init__(self):
        self.service = self.authenticate()
        # Initialize cache sync system for improved performance
        # Pass self to avoid circular import
        self.cache_sync = CalendarCacheSync(google_calendar=self)

    def authenticate(self):
        # Get calendar configuration
        calendar_config = config.get_section('calendar')
        
        creds = None
        token_path = calendar_config.get('token_file', 'token.pickle')
        credentials_path = calendar_config.get('credentials_file', 'credentials.json')
        scopes = calendar_config.get('scopes', [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/tasks'
        ])
        
        # Check if credentials.json exists
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Missing {credentials_path}. Please download your Google Calendar API credentials from the Google Cloud Console."
            )
        
        # Load existing token
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        # If credentials are invalid or expired, refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("[INFO] Refreshing Google Calendar credentials...")
                    creds.refresh(Request())
                    print("[INFO] Credentials refreshed successfully")
                except RefreshError as e:
                    print(f"[WARN] Failed to refresh credentials: {e}")
                    print("[INFO] Removing expired token and re-authenticating...")
                    # Remove the expired token file
                    if os.path.exists(token_path):
                        os.remove(token_path)
                    creds = None
            
            # If refresh failed or no credentials, start new OAuth flow
            if not creds or not creds.valid:
                print("[INFO] Starting Google Calendar authentication...")
                print("[INFO] Your web browser will open for authentication.")
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, scopes)
                creds = flow.run_local_server(port=0)
                print("[INFO] Authentication successful!")
            
            # Save the credentials for the next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
                print(f"[INFO] Credentials saved to {token_path}")

        return build('calendar', 'v3', credentials=creds)

    def find_free_time_slot(self, event_duration, date_obj):
        """Find free slots for the specified duration using local cache for improved performance."""
        # Use cache sync system for fast local access
        return self.cache_sync.find_free_time_slot(event_duration, date_obj)

    def create_event(self, summary, start_time_str, end_time_str):
        """Create event in Google Calendar and update local cache."""
        # Get timezone from config
        timezone = config.get('calendar.timezone', 'Europe/London')

        event = {
            'summary': summary,
            'start': {'dateTime': start_time_str.isoformat(), 'timeZone': timezone},
            'end': {'dateTime': end_time_str.isoformat(), 'timeZone': timezone},
        }

        created_event = self.service.events().insert(calendarId='primary', body=event).execute()

        # Also create in local cache for immediate consistency
        try:
            self.cache_sync.local_db.create_event(
                summary=summary,
                start_time=start_time_str.isoformat(),
                end_time=end_time_str.isoformat(),
                provider='google',
                google_event_id=created_event.get('id')
            )
        except Exception as e:
            print(f"[WARN] Failed to update local cache for new event: {e}")

        return f"The event '{created_event['summary']}' has been created."

    def delete_event(self, event_id: str) -> str:
        """Delete an event from Google Calendar and update local cache."""
        try:
            # Delete from Google Calendar
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()

            # Also mark as deleted in local cache
            try:
                # Find the event in local cache by Google event ID
                local_event = self.cache_sync.local_db.get_event_by_provider_id('google', event_id)
                if local_event:
                    self.cache_sync.local_db.update_event(
                        local_event['id'],
                        is_deleted=1,
                        sync_status='synced',
                        last_sync_at=datetime.now().isoformat()
                    )
            except Exception as e:
                print(f"[WARN] Failed to update local cache for deleted event: {e}")

            return f"Event has been deleted successfully."

        except Exception as e:
            error_msg = str(e)
            if "notFound" in error_msg:
                return "Event not found. It may have already been deleted."
            else:
                return f"Failed to delete event: {error_msg}"

    def update_event(self, event_id: str, summary: str = None, start_time: str = None,
                    end_time: str = None, description: str = None, location: str = None) -> str:
        """Update an event in Google Calendar and local cache."""
        try:
            # Get the existing event
            existing_event = self.service.events().get(calendarId='primary', eventId=event_id).execute()

            # Update only the provided fields
            if summary is not None:
                existing_event['summary'] = summary
            if description is not None:
                existing_event['description'] = description
            if location is not None:
                existing_event['location'] = location
            if start_time is not None or end_time is not None:
                # Update time fields
                if start_time is not None:
                    existing_event['start']['dateTime'] = start_time
                if end_time is not None:
                    existing_event['end']['dateTime'] = end_time

            # Update in Google Calendar
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=existing_event
            ).execute()

            # Also update in local cache
            try:
                local_event = self.cache_sync.local_db.get_event_by_provider_id('google', event_id)
                if local_event:
                    update_data = {
                        'sync_status': 'synced',
                        'last_sync_at': datetime.now().isoformat()
                    }
                    if summary is not None:
                        update_data['summary'] = summary
                    if description is not None:
                        update_data['description'] = description
                    if location is not None:
                        update_data['location'] = location
                    if start_time is not None:
                        update_data['start_time'] = start_time
                    if end_time is not None:
                        update_data['end_time'] = end_time

                    update_data['event_version'] = local_event.get('event_version', 1) + 1
                    self.cache_sync.local_db.update_event(local_event['id'], **update_data)
            except Exception as e:
                print(f"[WARN] Failed to update local cache for modified event: {e}")

            return f"The event '{updated_event.get('summary', 'Untitled')}' has been updated."

        except Exception as e:
            error_msg = str(e)
            if "notFound" in error_msg:
                return "Event not found. It may have already been deleted."
            else:
                return f"Failed to update event: {error_msg}"

    def find_event_by_summary(self, summary: str, date_obj: datetime = None) -> Optional[Dict]:
        """Find an event by its summary/title, optionally filtered by date."""
        try:
            # Get events for the specified date or next 7 days
            if date_obj:
                start_date = date_obj
                end_date = date_obj
            else:
                start_date = datetime.now()
                end_date = start_date + timedelta(days=7)

            tz = pytz.timezone(config.get('calendar.timezone', 'Europe/London'))
            start_datetime = tz.localize(datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0))
            end_datetime = tz.localize(datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59))

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Find events matching the summary (case-insensitive partial match)
            matching_events = []
            for event in events:
                event_summary = event.get('summary', '').lower()
                if summary.lower() in event_summary:
                    matching_events.append(event)

            return matching_events

        except Exception as e:
            print(f"[ERROR] Failed to find event by summary: {e}")
            return None

    def list_upcoming_events(self, max_results: int = 10) -> str:
        """List upcoming events for easy reference."""
        try:
            # Get events for the next 7 days
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)

            tz = pytz.timezone(config.get('calendar.timezone', 'Europe/London'))
            start_datetime = tz.localize(datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0))
            end_datetime = tz.localize(datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59))

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                singleEvents=True,
                orderBy='startTime',
                maxResults=max_results
            ).execute()

            events = events_result.get('items', [])

            if not events:
                return "No upcoming events found."

            response_lines = ["Here are your upcoming events:"]
            for i, event in enumerate(events, 1):
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'T' in start:
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%A %H:%M')
                else:
                    start_time = f"All day on {start}"

                summary = event.get('summary', 'Untitled Event')
                response_lines.append(f"{i}. {summary} - {start_time}")

            return "\n".join(response_lines)

        except Exception as e:
            return f"Failed to retrieve upcoming events: {str(e)}"

    # Cache management methods
    def refresh_cache(self):
        """Force refresh the local cache with Google Calendar data."""
        return self.cache_sync.force_refresh_cache()

    def get_cache_status(self):
        """Get current cache synchronization status."""
        return self.cache_sync.get_sync_status()

    def cleanup_cache(self, days_to_keep: int = 30):
        """Clean up old events from cache."""
        return self.cache_sync.cleanup_cache(days_to_keep)

    def export_cache(self, format: str = 'json'):
        """Export cached events."""
        return self.cache_sync.export_cache(format)

    def import_cache(self, data: str, format: str = 'json'):
        """Import events into cache."""
        return self.cache_sync.import_cache(data, format)

    def get_events_for_date(self, date_obj):
        """Retrieve all events for a specific date using local cache for improved performance."""
        # Use cache sync system for fast local access
        return self.cache_sync.get_events_for_date(date_obj)