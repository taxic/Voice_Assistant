# outlook_interface.py
import requests
import json
import os
import webbrowser
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from config_manager import config
import msal
import time

class OutlookInterface:
    """Interface for interacting with Microsoft Outlook/Graph API"""
    
    def __init__(self):
        """Initialize Outlook interface with Microsoft Graph credentials"""
        self.outlook_config = config.get_section('outlook', {})
        
        # Get credentials from environment variables or config
        self.client_id = os.getenv('OUTLOOK_CLIENT_ID') or self.outlook_config.get('client_id')
        self.client_secret = os.getenv('OUTLOOK_CLIENT_SECRET') or self.outlook_config.get('client_secret')
        self.tenant_id = os.getenv('OUTLOOK_TENANT_ID') or self.outlook_config.get('tenant_id', 'common')
        
        # Microsoft Graph API endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.graph_url = "https://graph.microsoft.com/v1.0"
        
        # Scopes needed for calendar access
        self.scopes = self.outlook_config.get('scopes', [
            "https://graph.microsoft.com/Calendars.ReadWrite",
            "https://graph.microsoft.com/User.Read"
        ])
        
        # Token cache file
        self.token_cache_file = self.outlook_config.get('token_cache_file', '.outlook_token_cache')
        
        # Initialize MSAL app
        self.app = None
        self.is_authenticated = False
        self.access_token = None
        
        if self.client_id:
            self._initialize_msal_app()
            self._load_token_cache()
            self.is_authenticated = self._check_authentication()
        else:
            print("[WARN] Outlook client ID not found. Set OUTLOOK_CLIENT_ID environment variable.")
    
    def _initialize_msal_app(self):
        """Initialize the MSAL application"""
        try:
            # Load token cache if it exists
            cache = msal.SerializableTokenCache()
            if os.path.exists(self.token_cache_file):
                with open(self.token_cache_file, 'r') as cache_file:
                    cache.deserialize(cache_file.read())
            
            if self.client_secret:
                # Confidential client app (with client secret)
                self.app = msal.ConfidentialClientApplication(
                    client_id=self.client_id,
                    client_credential=self.client_secret,
                    authority=self.authority,
                    token_cache=cache
                )
            else:
                # Public client app (without client secret)
                self.app = msal.PublicClientApplication(
                    client_id=self.client_id,
                    authority=self.authority,
                    token_cache=cache
                )
        except Exception as e:
            print(f"[ERROR] Failed to initialize MSAL app: {e}")
    
    def _load_token_cache(self):
        """Load and use cached tokens"""
        if not self.app:
            return
        
        try:
            # Try to get token silently
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    self.access_token = result["access_token"]
                    self._save_token_cache()
                    return True
        except Exception as e:
            print(f"[WARN] Failed to load cached token: {e}")
        return False
    
    def _save_token_cache(self):
        """Save token cache to file"""
        if not self.app:
            return
        
        try:
            with open(self.token_cache_file, 'w') as cache_file:
                cache_file.write(self.app.token_cache.serialize())
        except Exception as e:
            print(f"[WARN] Failed to save token cache: {e}")
    
    def authenticate(self):
        """Authenticate with Microsoft Graph API"""
        if not self.app:
            print("[ERROR] MSAL app not initialized. Check your client ID.")
            return False
        
        try:
            # Try interactive authentication
            if self.client_secret:
                # For confidential client, use client credentials flow
                result = self.app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            else:
                # For public client, use device code flow (better for voice assistants)
                flow = self.app.initiate_device_flow(scopes=self.scopes)
                if "user_code" not in flow:
                    raise Exception("Failed to create device flow")
                
                print(f"\n[INFO] To authenticate with Outlook:")
                print(f"1. Go to: {flow['verification_uri']}")
                print(f"2. Enter code: {flow['user_code']}")
                print("3. Complete authentication in your browser")
                print("4. Return here and wait for completion...\n")
                
                # Wait for user to complete authentication
                result = self.app.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self._save_token_cache()
                self.is_authenticated = True
                print("[INFO] Outlook authentication successful!")
                return True
            else:
                error = result.get("error_description", "Unknown error")
                print(f"[ERROR] Outlook authentication failed: {error}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Outlook authentication error: {e}")
            return False
    
    def _check_authentication(self):
        """Check if we have a valid token"""
        if not self.access_token:
            return False
        
        try:
            # Test the token by making a simple API call
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.graph_url}/me", headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make a request to Microsoft Graph API"""
        if not self.is_authenticated:
            print("[WARN] Not authenticated with Outlook. Call authenticate() first.")
            return None
        
        try:
            url = f"{self.graph_url}/{endpoint.lstrip('/')}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=15)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=15)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data, timeout=15)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code in [200, 201, 204]:
                return response.json() if response.content else {}
            elif response.status_code == 401:
                # Token expired, try to refresh
                print("[INFO] Token expired, attempting to refresh...")
                if self._refresh_token():
                    # Retry the request with new token
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    if method.upper() == "GET":
                        response = requests.get(url, headers=headers, timeout=15)
                    elif method.upper() == "POST":
                        response = requests.post(url, headers=headers, json=data, timeout=15)
                    # ... handle other methods if needed
                    
                    if response.status_code in [200, 201, 204]:
                        return response.json() if response.content else {}
                
                print("[ERROR] Authentication failed. Please re-authenticate.")
                self.is_authenticated = False
                return None
            else:
                print(f"[ERROR] Outlook API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Outlook API request failed: {e}")
            return None
    
    def _refresh_token(self):
        """Attempt to refresh the access token"""
        if not self.app:
            return False
        
        try:
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    self.access_token = result["access_token"]
                    self._save_token_cache()
                    return True
        except Exception as e:
            print(f"[WARN] Failed to refresh token: {e}")
        return False
    
    def get_calendars(self) -> List[Dict]:
        """Get list of user's calendars"""
        if not self.is_authenticated:
            return []
        
        response = self._make_request("GET", "me/calendars")
        if response and "value" in response:
            return response["value"]
        return []
    
    def get_primary_calendar_id(self) -> Optional[str]:
        """Get the primary calendar ID"""
        calendars = self.get_calendars()
        for calendar in calendars:
            if calendar.get("isDefaultCalendar", False):
                return calendar["id"]
        
        # If no default found, return the first calendar
        return calendars[0]["id"] if calendars else None
    
    def create_event(self, summary: str, start_time: datetime, end_time: datetime, 
                    description: str = "", location: str = "", calendar_id: str = None) -> str:
        """Create a new calendar event"""
        if not self.is_authenticated:
            return "Error: Not authenticated with Outlook"
        
        try:
            # Use primary calendar if none specified
            if not calendar_id:
                calendar_id = self.get_primary_calendar_id()
                if not calendar_id:
                    return "Error: No calendar found"
            
            # Format datetime for Microsoft Graph (ISO 8601 with timezone)
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            
            event_data = {
                "subject": summary,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC"
                }
            }
            
            if description:
                event_data["body"] = {
                    "contentType": "text",
                    "content": description
                }
            
            if location:
                event_data["location"] = {
                    "displayName": location
                }
            
            response = self._make_request("POST", f"me/calendars/{calendar_id}/events", event_data)
            
            if response:
                event_time = start_time.strftime("%A, %B %d at %H:%M")
                return f"Created Outlook event '{summary}' for {event_time}"
            else:
                return "Failed to create Outlook event"
                
        except Exception as e:
            print(f"[ERROR] Failed to create Outlook event: {e}")
            return f"Error creating Outlook event: {str(e)}"
    
    def get_events_for_date(self, date_obj: datetime) -> str:
        """Get events for a specific date"""
        if not self.is_authenticated:
            return "Error: Not authenticated with Outlook"
        
        try:
            # Set up date range (entire day)
            start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if start_of_day.tzinfo is None:
                start_of_day = start_of_day.replace(tzinfo=timezone.utc)
            if end_of_day.tzinfo is None:
                end_of_day = end_of_day.replace(tzinfo=timezone.utc)
            
            # Build query parameters
            params = {
                "$filter": f"start/dateTime ge '{start_of_day.isoformat()}' and start/dateTime le '{end_of_day.isoformat()}'",
                "$orderby": "start/dateTime",
                "$select": "subject,start,end,location,body"
            }
            
            # Build query string
            query_string = "&".join([f"{k}={urllib.parse.quote(v)}" for k, v in params.items()])
            endpoint = f"me/events?{query_string}"
            
            response = self._make_request("GET", endpoint)
            
            if not response or "value" not in response:
                return f"No Outlook events found for {date_obj.strftime('%A, %B %d, %Y')}"
            
            events = response["value"]
            if not events:
                return f"No Outlook events found for {date_obj.strftime('%A, %B %d, %Y')}"
            
            # Format events for response
            date_str = date_obj.strftime('%A, %B %d, %Y')
            event_list = [f"Outlook events for {date_str}:"]
            
            for event in events:
                subject = event.get("subject", "Untitled Event")
                start_dt = datetime.fromisoformat(event["start"]["dateTime"].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(event["end"]["dateTime"].replace('Z', '+00:00'))
                
                time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                location_str = ""
                if event.get("location") and event["location"].get("displayName"):
                    location_str = f" at {event['location']['displayName']}"
                
                event_list.append(f"• {time_str}: {subject}{location_str}")
            
            return "\n".join(event_list)
            
        except Exception as e:
            print(f"[ERROR] Failed to get Outlook events: {e}")
            return f"Error retrieving Outlook events: {str(e)}"
    
    def find_free_time_slot(self, duration_minutes: int, date_obj: datetime) -> Optional[str]:
        """Find a free time slot of specified duration on the given date"""
        if not self.is_authenticated:
            return None
        
        try:
            # Get events for the day
            start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if start_of_day.tzinfo is None:
                start_of_day = start_of_day.replace(tzinfo=timezone.utc)
            if end_of_day.tzinfo is None:
                end_of_day = end_of_day.replace(tzinfo=timezone.utc)
            
            params = {
                "$filter": f"start/dateTime ge '{start_of_day.isoformat()}' and start/dateTime le '{end_of_day.isoformat()}'",
                "$orderby": "start/dateTime",
                "$select": "start,end"
            }
            
            query_string = "&".join([f"{k}={urllib.parse.quote(v)}" for k, v in params.items()])
            response = self._make_request("GET", f"me/events?{query_string}")
            
            if not response:
                return None
            
            events = response.get("value", [])
            
            # Define working hours (9 AM to 6 PM)
            work_start = start_of_day.replace(hour=9)
            work_end = start_of_day.replace(hour=18)
            
            # Create list of busy times
            busy_times = []
            for event in events:
                event_start = datetime.fromisoformat(event["start"]["dateTime"].replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(event["end"]["dateTime"].replace('Z', '+00:00'))
                busy_times.append((event_start, event_end))
            
            # Sort busy times by start time
            busy_times.sort()
            
            # Find free slots
            current_time = work_start
            duration_delta = timedelta(minutes=duration_minutes)
            
            for start, end in busy_times:
                # Check if there's a gap before this event
                if current_time + duration_delta <= start:
                    return current_time.strftime("%H:%M")
                current_time = max(current_time, end)
            
            # Check if there's time at the end of the day
            if current_time + duration_delta <= work_end:
                return current_time.strftime("%H:%M")
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Failed to find free time slot: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID"""
        if not self.is_authenticated:
            return False
        
        response = self._make_request("DELETE", f"me/events/{event_id}")
        return response is not None
    
    def search_events(self, query: str, days_ahead: int = 30) -> List[Dict]:
        """Search for events containing the query string"""
        if not self.is_authenticated:
            return []
        
        try:
            # Set up date range for search
            start_date = datetime.now(timezone.utc)
            end_date = start_date + timedelta(days=days_ahead)
            
            params = {
                "$filter": f"start/dateTime ge '{start_date.isoformat()}' and start/dateTime le '{end_date.isoformat()}' and contains(subject, '{query}')",
                "$orderby": "start/dateTime",
                "$select": "id,subject,start,end,location"
            }
            
            query_string = "&".join([f"{k}={urllib.parse.quote(v)}" for k, v in params.items()])
            response = self._make_request("GET", f"me/events?{query_string}")
            
            if response and "value" in response:
                return response["value"]
            return []
            
        except Exception as e:
            print(f"[ERROR] Failed to search Outlook events: {e}")
            return []
    
    def get_user_info(self) -> Optional[Dict]:
        """Get basic user information"""
        if not self.is_authenticated:
            return None
        
        return self._make_request("GET", "me")
    
    def format_event_info(self, event: Dict) -> str:
        """Format event information for display"""
        try:
            subject = event.get("subject", "Untitled Event")
            start_dt = datetime.fromisoformat(event["start"]["dateTime"].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(event["end"]["dateTime"].replace('Z', '+00:00'))
            
            date_str = start_dt.strftime("%A, %B %d")
            time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
            
            location_str = ""
            if event.get("location") and event["location"].get("displayName"):
                location_str = f" at {event['location']['displayName']}"
            
            return f"• {date_str} {time_str}: {subject}{location_str}"
            
        except Exception as e:
            print(f"[WARN] Error formatting event info: {e}")
            return f"• {event.get('subject', 'Unknown event')}"
