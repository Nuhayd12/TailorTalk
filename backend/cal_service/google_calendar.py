import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import pytz

class GoogleCalendarService:
    """
    Robust Google Calendar service with comprehensive error handling
    and smart availability detection
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        
    def authenticate(self, credentials_file: str = "credentials.json") -> bool:
        """
        Authenticate with Google Calendar API
        Returns: True if successful, False otherwise
        """
        try:
            # Check for existing token
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    print("🔄 Refreshing expired credentials...")
                    self.credentials.refresh(Request())
                else:
                    if not os.path.exists(credentials_file):
                        print(f"❌ Credentials file '{credentials_file}' not found!")
                        print("📋 Please follow these steps:")
                        print("   1. Go to https://console.cloud.google.com/")
                        print("   2. Create project → Enable Calendar API")
                        print("   3. Create OAuth 2.0 credentials")
                        print("   4. Download as 'credentials.json' in root directory")
                        return False
                    
                    print("🔐 Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, self.SCOPES)
                    
                    # Use run_local_server with proper parameters
                    self.credentials = flow.run_local_server(
                        port=8080,
                        access_type='offline',
                        include_granted_scopes='true'
                    )
                
                # Save credentials for next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.credentials, token)
                    print("💾 Credentials saved for future use!")
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            print("✅ Successfully connected to Google Calendar!")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("\n🔧 Troubleshooting tips:")
            print("   • Make sure credentials.json is in the root directory")
            print("   • Check that Google Calendar API is enabled")
            print("   • Verify OAuth consent screen is configured")
            print("   • Try deleting token.pickle and re-authenticating")
            return False
    
    def get_availability(self, start_date: datetime, end_date: datetime, 
                        calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """
        Get free/busy information for a date range
        Returns list of busy periods
        """
        try:
            # Format dates for API
            start_time = start_date.isoformat() + 'Z'
            end_time = end_date.isoformat() + 'Z'
            
            # Get events in the time range
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            busy_periods = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                busy_periods.append({
                    'start': start,
                    'end': end,
                    'summary': event.get('summary', 'Busy'),
                    'id': event.get('id')
                })
            
            return busy_periods
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def find_free_slots(self, start_date: datetime, end_date: datetime, 
                       duration_minutes: int = 60, 
                       business_hours: tuple = (9, 17)) -> List[Dict[str, Any]]:
        """
        Find available time slots within business hours
        Returns list of available slots
        """
        busy_periods = self.get_availability(start_date, end_date)
        free_slots = []
        
        # Ensure we're working with UTC timezone
        utc = pytz.UTC
        if start_date.tzinfo is None:
            start_date = utc.localize(start_date)
        if end_date.tzinfo is None:
            end_date = utc.localize(end_date)
        
        current_time = start_date.replace(hour=business_hours[0], minute=0, second=0, microsecond=0)
        end_business_day = end_date.replace(hour=business_hours[1], minute=0, second=0, microsecond=0)
        
        # Convert busy periods to datetime objects with timezone
        busy_times = []
        for period in busy_periods:
            try:
                # Handle both date-only and datetime formats
                start_str = period['start']
                end_str = period['end']
                
                if 'T' in start_str:  # DateTime format
                    period_start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    period_end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                else:  # Date-only format
                    period_start = datetime.fromisoformat(start_str + 'T00:00:00+00:00')
                    period_end = datetime.fromisoformat(end_str + 'T23:59:59+00:00')
                
                # Ensure timezone awareness
                if period_start.tzinfo is None:
                    period_start = utc.localize(period_start)
                if period_end.tzinfo is None:
                    period_end = utc.localize(period_end)
                
                busy_times.append((period_start, period_end))
            except Exception as e:
                print(f"⚠️ Skipping invalid period: {period} - {e}")
                continue
        
        # Sort busy periods by start time
        busy_times.sort(key=lambda x: x[0])
        
        # Find gaps between busy periods
        while current_time < end_business_day:
            # Check if current time slot is available
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Skip weekends
            if current_time.weekday() >= 5:
                current_time += timedelta(days=1)
                current_time = current_time.replace(hour=business_hours[0], minute=0, second=0, microsecond=0)
                continue
            
            # Check if slot conflicts with any busy period
            is_free = True
            for busy_start, busy_end in busy_times:
                if (current_time < busy_end and slot_end > busy_start):
                    is_free = False
                    current_time = busy_end
                    break
            
            if is_free and slot_end.hour <= business_hours[1]:
                free_slots.append({
                    'start': current_time.isoformat(),
                    'end': slot_end.isoformat(),
                    'duration_minutes': duration_minutes
                })
                current_time += timedelta(minutes=30)  # Move to next potential slot
            else:
                current_time += timedelta(minutes=15)  # Small increment to find next opportunity
        
        return free_slots[:10]  # Return top 10 slots
    
    def create_event(self, title: str, start_time: datetime, end_time: datetime,
                    description: str = "", attendees: List[str] = None,
                    calendar_id: str = 'primary') -> Optional[str]:
        """
        Create a calendar event
        Returns event ID if successful, None otherwise
        """
        try:
            # Ensure timezone awareness
            utc = pytz.UTC
            if start_time.tzinfo is None:
                start_time = utc.localize(start_time)
            if end_time.tzinfo is None:
                end_time = utc.localize(end_time)
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            created_event = self.service.events().insert(
                calendarId=calendar_id, 
                body=event
            ).execute()
            
            return created_event.get('id')
            
        except HttpError as error:
            print(f"An error occurred creating event: {error}")
            return None
    
    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """
        Delete a calendar event
        Returns True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            return True
            
        except HttpError as error:
            print(f"An error occurred deleting event: {error}")
            return False