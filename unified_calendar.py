# unified_calendar.py
"""
Unified calendar interface that manages both Google Calendar and Outlook calendars.
Allows users to interact with both calendar systems through a single interface.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from calendar_interface import GoogleCalendar
from outlook_interface import OutlookInterface
from config_manager import config
import concurrent.futures
import dateparser

class UnifiedCalendar:
    """Unified interface for both Google Calendar and Outlook"""
    
    def __init__(self):
        """Initialize both calendar interfaces"""
        self.google_calendar = GoogleCalendar()
        self.outlook_calendar = OutlookInterface()
        
        # Get configuration
        self.calendar_config = config.get_section('unified_calendar', {})
        self.default_provider = self.calendar_config.get('default_provider', 'auto')
        self.sync_both = self.calendar_config.get('sync_both', True)
        self.prefer_google = self.calendar_config.get('prefer_google', True)
        
        # Check which calendars are available
        self.google_available = self.google_calendar.service is not None
        self.outlook_available = self.outlook_calendar.is_authenticated
        
        print(f"[INFO] Calendar availability - Google: {'Available' if self.google_available else 'Not available'}, Outlook: {'Available' if self.outlook_available else 'Not available'}")
    
    def get_available_calendars(self) -> Dict[str, bool]:
        """Get availability status of calendar providers"""
        return {
            'google': self.google_available,
            'outlook': self.outlook_available,
            'any_available': self.google_available or self.outlook_available
        }
    
    def create_event(self, summary: str, start_time: datetime, end_time: datetime,
                    description: str = "", location: str = "", provider: str = None) -> str:
        """Create an event in the specified calendar provider(s)"""
        
        if provider is None:
            provider = self.default_provider
        
        results = []
        
        # Determine which calendars to create events in
        if provider == 'google' and self.google_available:
            result = self.google_calendar.create_event(summary, start_time, end_time)
            results.append(f"Google: {result}")
        
        elif provider == 'outlook' and self.outlook_available:
            result = self.outlook_calendar.create_event(summary, start_time, end_time, description, location)
            results.append(f"Outlook: {result}")
        
        elif provider == 'both':
            # Create in both calendars
            if self.google_available:
                result = self.google_calendar.create_event(summary, start_time, end_time)
                results.append(f"Google: {result}")
            
            if self.outlook_available:
                result = self.outlook_calendar.create_event(summary, start_time, end_time, description, location)
                results.append(f"Outlook: {result}")
        
        elif provider == 'auto':
            # Auto-select based on availability and preference
            if self.prefer_google and self.google_available:
                result = self.google_calendar.create_event(summary, start_time, end_time)
                results.append(result)
            elif self.outlook_available:
                result = self.outlook_calendar.create_event(summary, start_time, end_time, description, location)
                results.append(result)
            elif self.google_available:
                result = self.google_calendar.create_event(summary, start_time, end_time)
                results.append(result)
            else:
                return "Error: No calendar providers are available"
            
            # Optionally sync to both if configured
            if self.sync_both and len(results) == 1:
                if self.prefer_google and self.google_available and self.outlook_available:
                    # Already created in Google, also create in Outlook
                    result = self.outlook_calendar.create_event(summary, start_time, end_time, description, location)
                    results.append(f"Also synced to Outlook: {result}")
                elif not self.prefer_google and self.outlook_available and self.google_available:
                    # Already created in Outlook, also create in Google
                    result = self.google_calendar.create_event(summary, start_time, end_time)
                    results.append(f"Also synced to Google: {result}")
        
        else:
            # Invalid provider or provider not available
            available_providers = []
            if self.google_available:
                available_providers.append("Google")
            if self.outlook_available:
                available_providers.append("Outlook")
            
            if not available_providers:
                return "Error: No calendar providers are available"
            else:
                return f"Error: Provider '{provider}' not available. Available: {', '.join(available_providers)}"
        
        if not results:
            return "Error: No events were created"
        
        return " | ".join(results)
    
    def get_events_for_date(self, date_obj: datetime, provider: str = None) -> str:
        """Get events for a specific date from specified calendar provider(s)"""
        
        if provider is None:
            provider = self.default_provider
        
        results = []
        
        def get_google_events():
            if self.google_available:
                return self.google_calendar.get_events_for_date(date_obj)
            return None
        
        def get_outlook_events():
            if self.outlook_available:
                return self.outlook_calendar.get_events_for_date(date_obj)
            return None
        
        if provider == 'google' and self.google_available:
            result = get_google_events()
            if result:
                results.append(result)
        
        elif provider == 'outlook' and self.outlook_available:
            result = get_outlook_events()
            if result:
                results.append(result)
        
        elif provider == 'both' or provider == 'auto':
            # Get events from both calendars concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = {}
                
                if self.google_available:
                    futures['google'] = executor.submit(get_google_events)
                
                if self.outlook_available:
                    futures['outlook'] = executor.submit(get_outlook_events)
                
                # Collect results
                for calendar_type, future in futures.items():
                    try:
                        result = future.result(timeout=10)
                        if result and "No" not in result:  # Skip "No events found" messages
                            results.append(result)
                    except Exception as e:
                        print(f"[ERROR] Failed to get {calendar_type} events: {e}")
        
        if not results:
            date_str = date_obj.strftime('%A, %B %d, %Y')
            return f"No events found for {date_str}"
        
        return "\n\n".join(results)
    
    def find_free_time_slot(self, duration_minutes: int, date_obj: datetime, provider: str = None) -> Optional[str]:
        """Find a free time slot considering events from specified calendar provider(s)"""
        
        if provider is None:
            provider = self.default_provider
        
        # Collect busy times from all relevant calendars
        all_busy_times = []
        
        def get_google_busy_times():
            if self.google_available:
                return self.google_calendar.find_free_time_slot(duration_minutes, date_obj.date())
            return None
        
        def get_outlook_busy_times():
            if self.outlook_available:
                return self.outlook_calendar.find_free_time_slot(duration_minutes, date_obj)
            return None
        
        if provider in ['google', 'auto', 'both'] and self.google_available:
            google_free_time = get_google_busy_times()
            if google_free_time and provider == 'google':
                return google_free_time
        
        if provider in ['outlook', 'auto', 'both'] and self.outlook_available:
            outlook_free_time = get_outlook_busy_times()
            if outlook_free_time and provider == 'outlook':
                return outlook_free_time
        
        # For 'auto' or 'both', we need to implement a more sophisticated algorithm
        # that considers events from both calendars. This is a simplified version.
        if provider in ['auto', 'both']:
            # Try to find a time that's free in the primary calendar
            primary_provider = 'google' if self.prefer_google and self.google_available else 'outlook'
            
            if primary_provider == 'google' and self.google_available:
                return get_google_busy_times()
            elif primary_provider == 'outlook' and self.outlook_available:
                return get_outlook_busy_times()
        
        return None
    
    def search_events(self, query: str, days_ahead: int = 30, provider: str = None) -> List[Dict]:
        """Search for events across specified calendar provider(s)"""
        
        if provider is None:
            provider = self.default_provider
        
        results = []
        
        def search_google_events():
            if self.google_available:
                # Google Calendar interface doesn't have a search method in the current implementation
                # This would need to be implemented in the GoogleCalendar class
                return []
            return []
        
        def search_outlook_events():
            if self.outlook_available:
                return self.outlook_calendar.search_events(query, days_ahead)
            return []
        
        if provider == 'google' and self.google_available:
            results.extend(search_google_events())
        
        elif provider == 'outlook' and self.outlook_available:
            results.extend(search_outlook_events())
        
        elif provider in ['both', 'auto']:
            # Search both calendars concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                
                if self.google_available:
                    futures.append(executor.submit(search_google_events))
                
                if self.outlook_available:
                    futures.append(executor.submit(search_outlook_events))
                
                # Collect results
                for future in futures:
                    try:
                        result = future.result(timeout=10)
                        results.extend(result)
                    except Exception as e:
                        print(f"[ERROR] Failed to search events: {e}")
        
        return results
    
    def get_calendar_summary(self, days_ahead: int = 7) -> str:
        """Get a summary of upcoming events from all available calendars"""
        
        summary_parts = []
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        # Get summary from each available calendar
        if self.google_available:
            try:
                # This would need to be implemented in the GoogleCalendar class
                summary_parts.append("Google Calendar: Available")
            except Exception as e:
                print(f"[ERROR] Failed to get Google calendar summary: {e}")
        
        if self.outlook_available:
            try:
                user_info = self.outlook_calendar.get_user_info()
                if user_info:
                    display_name = user_info.get('displayName', 'Unknown User')
                    summary_parts.append(f"Outlook Calendar: Connected as {display_name}")
                else:
                    summary_parts.append("Outlook Calendar: Connected")
            except Exception as e:
                print(f"[ERROR] Failed to get Outlook calendar summary: {e}")
        
        if not summary_parts:
            return "No calendar providers are currently available"
        
        return "\n".join(summary_parts)
    
    def authenticate_missing_providers(self) -> str:
        """Attempt to authenticate any missing calendar providers"""
        
        results = []
        
        if not self.google_available:
            try:
                # Google Calendar authentication happens automatically during initialization
                # If it failed initially, we might need to re-initialize
                self.google_calendar = GoogleCalendar()
                self.google_available = self.google_calendar.service is not None
                if self.google_available:
                    results.append("SUCCESS: Google Calendar authentication successful")
                else:
                    results.append("FAILED: Google Calendar authentication failed")
            except Exception as e:
                results.append(f"ERROR: Google Calendar error: {e}")
        
        if not self.outlook_available:
            try:
                success = self.outlook_calendar.authenticate()
                self.outlook_available = success
                if success:
                    results.append("SUCCESS: Outlook Calendar authentication successful")
                else:
                    results.append("FAILED: Outlook Calendar authentication failed")
            except Exception as e:
                results.append(f"ERROR: Outlook Calendar error: {e}")
        
        if not results:
            return "All available calendar providers are already authenticated"
        
        return "\n".join(results)
    
    def get_provider_status(self) -> str:
        """Get detailed status of all calendar providers"""
        
        status_parts = []
        
        # Google Calendar status
        if self.google_available:
            status_parts.append("OK: Google Calendar: Connected and ready")
        else:
            status_parts.append("ERROR: Google Calendar: Not available (check credentials.json and authentication)")
        
        # Outlook Calendar status
        if self.outlook_available:
            try:
                user_info = self.outlook_calendar.get_user_info()
                if user_info:
                    display_name = user_info.get('displayName', 'Unknown User')
                    email = user_info.get('mail') or user_info.get('userPrincipalName', 'Unknown Email')
                    status_parts.append(f"✓ Outlook Calendar: Connected as {display_name} ({email})")
                else:
                    status_parts.append("OK: Outlook Calendar: Connected")
            except Exception as e:
                status_parts.append(f"WARNING: Outlook Calendar: Connected but error getting user info: {e}")
        else:
            status_parts.append("ERROR: Outlook Calendar: Not available (check OUTLOOK_CLIENT_ID and authentication)")
        
        # Configuration status
        status_parts.append(f"\nConfiguration:")
        status_parts.append(f"  • Default provider: {self.default_provider}")
        status_parts.append(f"  • Prefer Google: {self.prefer_google}")
        status_parts.append(f"  • Sync both calendars: {self.sync_both}")
        
        return "\n".join(status_parts)
    
    def recommend_provider(self, operation: str = "create") -> str:
        """Recommend the best provider for a given operation"""
        
        if not self.google_available and not self.outlook_available:
            return "none"
        
        if self.google_available and not self.outlook_available:
            return "google"
        
        if self.outlook_available and not self.google_available:
            return "outlook"
        
        # Both are available - make recommendation based on operation and preferences
        if operation in ["create", "add"]:
            return "google" if self.prefer_google else "outlook"
        elif operation in ["view", "list", "get"]:
            return "both"  # Show events from all calendars
        elif operation in ["search", "find"]:
            return "both"  # Search across all calendars
        else:
            return "auto"  # Let the system decide
