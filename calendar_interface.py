from __future__ import print_function
from datetime import datetime
import os.path
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
import pytz
from config_manager import config

class GoogleCalendar:
    def __init__(self):
        self.service = self.authenticate()

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

    def create_event(self, summary, start_time_str, end_time_str):
        # Get timezone from config
        timezone = config.get('calendar.timezone', 'Europe/London')
        
        event = {
            'summary': summary,
            'start': {'dateTime': start_time_str.isoformat(), 'timeZone': timezone},
            'end': {'dateTime': end_time_str.isoformat(), 'timeZone': timezone},
        }

        event = self.service.events().insert(calendarId='primary', body=event).execute()
        return f"The event '{event['summary']}' has been created."

    def get_events_for_date(self, date_obj):
        """Retrieve all events for a specific date (datetime object)."""
        # Get timezone from config
        timezone_name = config.get('calendar.timezone', 'Europe/London')
        
        # Define start and end of the day in RFC3339 format
        tz = pytz.timezone(timezone_name)
        start_of_day = tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
        end_of_day = tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59))

        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            if date_obj.strftime('%A') == datetime.now().strftime('%A'):
                return "You have no events today."
            else:
                return f"You have no events on {date_obj.strftime('%A')}."

        response_lines = [f"Here are your events on {date_obj.strftime('%A')}:"]

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_time = datetime.fromisoformat(start).strftime('%H:%M') if 'T' in start else "All-day"
            summary = event.get('summary', 'No Title')
            response_lines.append(f"• {summary} at {start_time}")

        return "\n".join(response_lines)