import os
import json
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
    Production-ready Google Calendar service with deployment support
    Handles both local development and cloud deployment scenarios
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        
    def get_google_credentials(self) -> Optional[Dict]:
        """
        Get Google credentials from environment or file
        Supports both production (env vars) and development (files)
        """
        try:
            # Production: Try environment variable first
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if creds_json:
                print("📡 Using Google credentials from environment variable")
                return json.loads(creds_json)
            
            # Development: Fallback to credentials file
            credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
            
            # Check in current directory
            if os.path.exists(credentials_file):
                print(f"📁 Using credentials file: {credentials_file}")
                with open(credentials_file, 'r') as f:
                    return json.load(f)
            
            # Check in backend/api directory
            api_creds_path = os.path.join('backend', 'api', credentials_file)
            if os.path.exists(api_creds_path):
                print(f"📁 Using credentials file: {api_creds_path}")
                with open(api_creds_path, 'r') as f:
                    return json.load(f)
                    
            return None
            
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return None
    
    def authenticate(self, credentials_file: str = "credentials.json") -> bool:
        """
        Authenticate with Google Calendar API
        Supports both production and development environments
        """
        try:
            # Check for existing token (only in development)
            token_path = 'token.pickle'
            if not self._is_production() and os.path.exists(token_path):
                try:
                    with open(token_path, 'rb') as token:
                        self.credentials = pickle.load(token)
                        print("💾 Loaded existing credentials from token.pickle")
                except Exception as e:
                    print(f"⚠️ Error loading token.pickle: {e}")
                    # Continue with fresh authentication
            
            # If no valid credentials, get new ones
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    print("🔄 Refreshing expired credentials...")
                    try:
                        self.credentials.refresh(Request())
                    except Exception as e:
                        print(f"❌ Token refresh failed: {e}")
                        self.credentials = None
                
                if not self.credentials:
                    # Get credentials configuration
                    creds_config = self.get_google_credentials()
                    if not creds_config:
                        return self._handle_missing_credentials()
                    
                    if self._is_production():
                        return self._authenticate_production(creds_config)
                    else:
                        return self._authenticate_development(creds_config)
                
                # Save credentials for development only
                if not self._is_production() and self.credentials:
                    try:
                        with open(token_path, 'wb') as token:
                            pickle.dump(self.credentials, token)
                            print("💾 Credentials saved for future use!")
                    except Exception as e:
                        print(f"⚠️ Could not save token: {e}")
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            print("✅ Successfully connected to Google Calendar!")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def _is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER') or os.getenv('HEROKU_APP_NAME') or os.getenv('PORT')
    
    def _authenticate_production(self, creds_config: Dict) -> bool:
        """
        Handle authentication for production deployment
        Uses service account or pre-authenticated tokens
        """
        try:
            # For production, we need to use a different approach
            # Since OAuth flow requires user interaction
            
            # Option 1: Use environment variables for pre-authenticated tokens
            token_data = os.getenv('GOOGLE_TOKEN_JSON')
            if token_data:
                token_info = json.loads(token_data)
                self.credentials = Credentials.from_authorized_user_info(token_info, self.SCOPES)
                if self.credentials.expired:
                    self.credentials.refresh(Request())
                return True
            
            # Option 2: Demo mode for production without full OAuth
            print("⚠️ Production deployment detected but no pre-authenticated token found")
            print("🔧 Consider using a service account or demo mode")
            return self._setup_demo_mode()
            
        except Exception as e:
            print(f"❌ Production authentication failed: {e}")
            return self._setup_demo_mode()
    
    def _authenticate_development(self, creds_config: Dict) -> bool:
        """Handle authentication for local development"""
        try:
            print("🔐 Starting OAuth flow for development...")
            
            # Write credentials to temporary file for OAuth flow
            temp_creds_file = 'temp_credentials.json'
            with open(temp_creds_file, 'w') as f:
                json.dump(creds_config, f)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                temp_creds_file, self.SCOPES)
            
            # Use run_local_server with proper parameters
            self.credentials = flow.run_local_server(
                port=8080,
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Clean up temporary file
            try:
                os.remove(temp_creds_file)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"❌ Development authentication failed: {e}")
            return False
    
    def _setup_demo_mode(self) -> bool:
        """Setup demo mode when full authentication isn't available"""
        print("🎭 Setting up demo mode...")
        self.service = None  # Will trigger demo responses
        return True
    
    def _handle_missing_credentials(self) -> bool:
        """Handle missing credentials scenario"""
        print("❌ No Google credentials found!")
        
        if self._is_production():
            print("📋 For production deployment, set these environment variables:")
            print("   GOOGLE_CREDENTIALS_JSON='{\"installed\":{\"client_id\":\"...\"}}'")
            print("   GOOGLE_TOKEN_JSON='{\"token\":\"...\",\"refresh_token\":\"...\"}'")
        else:
            print("📋 For local development:")
            print("   1. Go to https://console.cloud.google.com/")
            print("   2. Create project → Enable Calendar API")
            print("   3. Create OAuth 2.0 credentials")
            print("   4. Download as 'credentials.json' in root directory")
        
        return self._setup_demo_mode()
    
    def get_availability(self, start_date: datetime, end_date: datetime, 
                        calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """
        Get free/busy information for a date range
        Returns list of busy periods (with demo fallback)
        """
        if not self.service:
            return self._demo_busy_periods(start_date, end_date)
        
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
            print(f"📅 Calendar API error: {error}")
            return self._demo_busy_periods(start_date, end_date)
    
    def _demo_busy_periods(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate demo busy periods for demonstration"""
        busy_periods = []
        
        # Add some demo busy slots
        demo_start = start_date.replace(hour=10, minute=0, second=0, microsecond=0)
        demo_end = demo_start + timedelta(hours=1)
        
        busy_periods.append({
            'start': demo_start.isoformat() + 'Z',
            'end': demo_end.isoformat() + 'Z',
            'summary': 'Demo Meeting (Calendar Demo Mode)',
            'id': 'demo_event_1'
        })
        
        return busy_periods
    
    def find_free_slots(self, start_date: datetime, end_date: datetime, 
                       duration_minutes: int = 60, 
                       business_hours: tuple = (9, 17)) -> List[Dict[str, Any]]:
        """
        Find available time slots within business hours
        Returns list of available slots (with demo fallback)
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
        Returns event ID if successful, None otherwise (with demo fallback)
        """
        if not self.service:
            print("🎭 Demo Mode: Event would be created -", title)
            return f"demo_event_{int(start_time.timestamp())}"
        
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
            print(f"📅 Calendar API error creating event: {error}")
            return None
    
    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """
        Delete a calendar event
        Returns True if successful, False otherwise (with demo fallback)
        """
        if not self.service:
            print("🎭 Demo Mode: Event would be deleted -", event_id)
            return True
        
        try:
            self.service.events().delete(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            return True
            
        except HttpError as error:
            print(f"📅 Calendar API error deleting event: {error}")
            return False
    
    def get_authorization_url(self) -> str:
        """
        Get OAuth authorization URL for Google Calendar
        """
        try:
            creds_config = self.get_google_credentials()
            if not creds_config:
                raise Exception("No Google credentials configuration found")
            
            # Create flow
            flow = InstalledAppFlow.from_client_config(
                creds_config, 
                self.SCOPES,
                redirect_uri=self._get_redirect_uri()
            )
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            return auth_url
            
        except Exception as e:
            print(f"❌ Error creating authorization URL: {e}")
            raise e
    
    def handle_oauth_callback(self, authorization_code: str) -> bool:
        """
        Handle OAuth callback and exchange code for tokens
        """
        try:
            creds_config = self.get_google_credentials()
            if not creds_config:
                return False
            
            # Create flow
            flow = InstalledAppFlow.from_client_config(
                creds_config, 
                self.SCOPES,
                redirect_uri=self._get_redirect_uri()
            )
            
            # Exchange code for tokens
            flow.fetch_token(code=authorization_code)
            self.credentials = flow.credentials
            
            # Initialize service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            # Save token in production environment (as env var)
            if self._is_production():
                # In production, you might want to store this securely
                print("✅ Calendar connected successfully in production")
            else:
                # Save token locally for development
                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.credentials, token)
                print("✅ Calendar connected and token saved locally")
            
            return True
            
        except Exception as e:
            print(f"❌ Error handling OAuth callback: {e}")
            return False
    
    def _get_redirect_uri(self) -> str:
        """Get the appropriate redirect URI for current environment"""
        if self._is_production():
            # Production Railway URL
            return "https://tailortalk-production.up.railway.app/auth/callback"
        else:
            # Local development
            return "http://localhost:8000/auth/callback"