from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime, timedelta
import re
import json
from enum import Enum
import pytz

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Import our calendar service
import sys
import os

# Add proper path handling for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

try:
    from cal_service.google_calendar import GoogleCalendarService
except ImportError:
    try:
        from backend.cal_service.google_calendar import GoogleCalendarService
    except ImportError:
        # Fallback path for deployment
        cal_service_path = os.path.join(backend_dir, 'cal_service', 'google_calendar.py')
        import importlib.util
        spec = importlib.util.spec_from_file_location("google_calendar", cal_service_path)
        cal_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cal_module)
        GoogleCalendarService = cal_module.GoogleCalendarService

class SmartAgentState(TypedDict):
    """Simplified state management"""
    conversation_history: List[Dict[str, str]]
    extracted_info: Dict[str, Any]
    available_slots: List[Dict[str, Any]]
    session_context: Dict[str, Any]

class SmartTailorTalkAgent:
    """
    LLM-driven intelligent conversational agent for calendar booking
    """
    
    def __init__(self, openai_api_key: str, timezone: str = "GMT"):
        print(f"🧠 Initializing Smart TailorTalk Agent with timezone: {timezone}...")
        
        # Set timezone
        self.timezone = timezone
        self.tz = self._get_timezone_object(timezone)
        
        # Get current date/time in the specified timezone
        self.current_time = datetime.now(self.tz)
        print(f"📅 Current time in {timezone}: {self.current_time.strftime('%A, %B %d, %Y at %I:%M %p')}")
        
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o-mini",
            temperature=0.3
        )
        
        # Initialize calendar service
        self.calendar_service = GoogleCalendarService()
        root_credentials = os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json')
        if os.path.exists(root_credentials):
            self.calendar_service.authenticate(root_credentials)
        else:
            self.calendar_service.authenticate()
        
        # Setup tools and agent
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()
        
        print("✅ Smart TailorTalk Agent ready!")
    
    def _get_timezone_object(self, timezone_str: str):
        """Get timezone object from string"""
        timezone_map = {
            'GMT': pytz.UTC,
            'UTC': pytz.UTC,
            'IST': pytz.timezone('Asia/Kolkata'),
            'AST': pytz.timezone('Canada/Atlantic'),  # Fixed: Atlantic Standard Time
            'EST': pytz.timezone('US/Eastern'),
            'PST': pytz.timezone('US/Pacific'),
            'CST': pytz.timezone('US/Central'),
            'MST': pytz.timezone('US/Mountain'),
            'AEST': pytz.timezone('Australia/Sydney'),  # Australian Eastern Standard Time
            'JST': pytz.timezone('Asia/Tokyo'),  # Japan Standard Time
            'CET': pytz.timezone('Europe/Paris'),  # Central European Time
        }
        
        try:
            return timezone_map.get(timezone_str.upper(), pytz.UTC)
        except Exception as e:
            print(f"⚠️ Timezone error for {timezone_str}: {e}. Falling back to UTC.")
            return pytz.UTC
        
    def set_timezone(self, timezone: str):
        """Change the timezone for the agent"""
        self.timezone = timezone
        self.tz = self._get_timezone_object(timezone)
        self.current_time = datetime.now(self.tz)
        print(f"🕐 Timezone changed to {timezone}. Current time: {self.current_time.strftime('%A, %B %d, %Y at %I:%M %p')}")
    
    def _create_tools(self):
        """Create tools for the agent to use"""

        @tool
        def search_available_slots(date_preference: str, duration_minutes: int = 60) -> str:
            """
            Search for available calendar slots based on user's date preference.
            
            Args:
                date_preference: Natural language date like 'tomorrow', 'next Friday', '29th June', 'today'
                duration_minutes: Meeting duration in minutes (default 60)
            
            Returns:
                JSON string with available slots or error message
            """
            try:
                print(f"🔍 Searching slots for: '{date_preference}' with duration {duration_minutes} minutes")
                
                # Parse the date preference
                start_date, end_date = self._parse_smart_date(date_preference)
                
                print(f"📅 Parsed search range: {start_date} to {end_date}")
                
                # Convert to UTC for calendar service (Google Calendar works in UTC)
                start_utc = start_date.astimezone(pytz.UTC)
                end_utc = end_date.astimezone(pytz.UTC)
                
                print(f"🌍 UTC search range: {start_utc} to {end_utc}")
                
                # Get free slots from calendar service
                free_slots = self.calendar_service.find_free_slots(
                    start_utc.replace(tzinfo=None),  # Remove timezone for the calendar service
                    end_utc.replace(tzinfo=None), 
                    duration_minutes
                )
                
                print(f"📊 Found {len(free_slots)} raw free slots")
                
                if not free_slots:
                    return json.dumps({
                        "success": False,
                        "message": f"No available slots found for {date_preference}. The calendar might be fully booked or outside business hours.",
                        "search_date": start_date.strftime('%A, %B %d, %Y'),
                        "timezone": self.timezone,
                        "debug_info": f"Searched {start_utc} to {end_utc} UTC"
                    })
                
                # Convert slots to user's timezone for display
                slots_info = []
                for i, slot in enumerate(free_slots[:10]):  # Limit to 10 slots
                    try:
                        # Parse slot times (they come back as UTC strings)
                        slot_start_utc = datetime.fromisoformat(slot['start']).replace(tzinfo=pytz.UTC)
                        slot_end_utc = datetime.fromisoformat(slot['end']).replace(tzinfo=pytz.UTC)
                        
                        # Convert to user's timezone
                        slot_start_local = slot_start_utc.astimezone(self.tz)
                        slot_end_local = slot_end_utc.astimezone(self.tz)
                        
                        # Format for display
                        date_display = slot_start_local.strftime('%A, %B %d, %Y')
                        time_display = f"{slot_start_local.strftime('%I:%M %p')} - {slot_end_local.strftime('%I:%M %p')} ({self.timezone})"
                        
                        slots_info.append({
                            "slot_number": i + 1,
                            "date": date_display,
                            "time": time_display,
                            "start": slot['start'],  # Keep UTC for booking
                            "end": slot['end'],      # Keep UTC for booking
                            "duration_minutes": duration_minutes,
                            "display_full": f"{date_display} at {slot_start_local.strftime('%I:%M %p')} ({self.timezone})"
                        })
                        
                    except Exception as slot_error:
                        print(f"⚠️ Error processing slot {i}: {slot_error}")
                        continue
                
                if not slots_info:
                    return json.dumps({
                        "success": False,
                        "message": f"Found slots but couldn't process them for display. Please try a different time range.",
                        "search_date": start_date.strftime('%A, %B %d, %Y'),
                        "timezone": self.timezone
                    })
                
                return json.dumps({
                    "success": True,
                    "message": f"Found {len(slots_info)} available slots for {date_preference}",
                    "slots": slots_info,
                    "search_date": start_date.strftime('%A, %B %d, %Y'),
                    "timezone": self.timezone,
                    "total_found": len(free_slots)
                })
                
            except Exception as e:
                print(f"❌ Error in search_available_slots: {e}")
                return json.dumps({
                    "success": False,
                    "message": f"Error searching calendar: {str(e)}",
                    "debug_info": f"Date preference: {date_preference}, Duration: {duration_minutes}"
                })

        @tool
        def book_meeting(slot_start: str, slot_end: str, title: str = "Meeting", description: str = "") -> str:
            """
            Book a meeting in the calendar.
            
            Args:
                slot_start: ISO format start time (UTC)
                slot_end: ISO format end time (UTC)
                title: Meeting title
                description: Meeting description
            
            Returns:
                JSON string with booking result
            """
            try:
                start_time = datetime.fromisoformat(slot_start)
                end_time = datetime.fromisoformat(slot_end)
                
                # Convert to user's timezone for display
                start_local = start_time.replace(tzinfo=pytz.UTC).astimezone(self.tz)
                
                event_id = self.calendar_service.create_event(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    description=description + f" (Scheduled via TailorTalk in {self.timezone})"
                )
                
                if event_id:
                    return json.dumps({
                        "success": True,
                        "message": f"✅ Meeting '{title}' successfully booked for {start_local.strftime('%A, %B %d at %I:%M %p')} {self.timezone}",
                        "event_id": event_id,
                        "local_time": start_local.strftime('%A, %B %d at %I:%M %p'),
                        "timezone": self.timezone
                    })
                else:
                    return json.dumps({
                        "success": False,
                        "message": "Failed to create calendar event. Please try again."
                    })
                    
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": f"Error booking meeting: {str(e)}"
                })
        
        @tool
        def get_current_time_info() -> str:
            """
            Get current date and time information in the user's timezone.
            
            Returns:
                JSON string with current time info
            """
            current = datetime.now(self.tz)
            
            return json.dumps({
                "success": True,
                "current_date": current.strftime('%A, %B %d, %Y'),
                "current_time": current.strftime('%I:%M %p'),
                "timezone": self.timezone,
                "iso_format": current.isoformat(),
                "day_of_week": current.strftime('%A'),
                "message": f"Current time is {current.strftime('%A, %B %d, %Y at %I:%M %p')} {self.timezone}"
            })
        
        @tool
        def change_timezone(new_timezone: str) -> str:
            """
            Change the timezone for the conversation.
            
            Args:
                new_timezone: Timezone code (GMT, IST, AST, EST, PST, etc.)
            
            Returns:
                JSON string with timezone change result
            """
            try:
                old_timezone = self.timezone
                self.set_timezone(new_timezone)
                
                return json.dumps({
                    "success": True,
                    "message": f"Timezone changed from {old_timezone} to {new_timezone}",
                    "old_timezone": old_timezone,
                    "new_timezone": new_timezone,
                    "current_time": self.current_time.strftime('%A, %B %d, %Y at %I:%M %p')
                })
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": f"Error changing timezone: {str(e)}"
                })
                
        # Add these new tools to the _create_tools method

        @tool
        def get_calendar_events(date_preference: str = "today", days_ahead: int = 1) -> str:
            """Get calendar events with proper timezone and format handling"""
            try:
                # Parse the date preference
                start_date, end_date = self._parse_smart_date(date_preference)
                
                # For single day requests, ensure we only look at that day
                if date_preference.lower() in ["today", "tomorrow"] and days_ahead == 1:
                    end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                elif days_ahead > 1:
                    end_date = start_date + timedelta(days=days_ahead - 1)
                    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # Convert to UTC for Google Calendar API (Google expects UTC)
                start_utc = start_date.astimezone(pytz.UTC)
                end_utc = end_date.astimezone(pytz.UTC)
                
                print(f"🔍 Fetching events: {start_utc.isoformat()} to {end_utc.isoformat()}")
                
                # Get events from Google Calendar API
                events_result = self.calendar_service.service.events().list(
                    calendarId='primary',
                    timeMin=start_utc.isoformat(),
                    timeMax=end_utc.isoformat(),
                    singleEvents=True,
                    orderBy='startTime',
                    maxResults=50
                ).execute()
                
                events = events_result.get('items', [])
                print(f"📅 Google Calendar returned {len(events)} events")
                
                if not events:
                    return json.dumps({
                        "success": True,
                        "events": [],
                        "message": f"No events found for {date_preference}",
                        "timezone_note": f"Searched in {self.timezone}",
                        "search_range": f"{start_date.strftime('%A, %B %d, %Y')} ({self.timezone})"
                    })
                
                events_with_timezone = []
                for event in events:
                    try:
                        # Get event times
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        end = event['end'].get('dateTime', event['end'].get('date'))
                        
                        if 'T' in start:  # DateTime event (not all-day)
                            # Parse datetime - handle both Z and timezone offset formats
                            if start.endswith('Z'):
                                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                            else:
                                start_dt = datetime.fromisoformat(start)
                            
                            if end.endswith('Z'):
                                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                            else:
                                end_dt = datetime.fromisoformat(end)
                            
                            # Convert to user's timezone for display
                            user_start = start_dt.astimezone(self.tz)
                            user_end = end_dt.astimezone(self.tz)
                            
                            # Format in 12-hour AM/PM format
                            start_time_12h = user_start.strftime('%I:%M %p').lstrip('0')
                            end_time_12h = user_end.strftime('%I:%M %p').lstrip('0')
                            
                            time_display = f"{start_time_12h} - {end_time_12h} ({self.timezone})"
                            date_display = user_start.strftime('%A, %B %d, %Y')
                            
                        else:  # All-day event
                            event_date = datetime.fromisoformat(start)
                            date_display = event_date.strftime('%A, %B %d, %Y')
                            time_display = "All day"
                        
                        events_with_timezone.append({
                            "title": event.get('summary', 'Untitled Event'),
                            "start_time": time_display,
                            "date": date_display,
                            "description": event.get('description', ''),
                            "location": event.get('location', ''),
                            "calendar_link": event.get('htmlLink', ''),
                            "event_id": event.get('id', '')
                        })
                        
                    except Exception as e:
                        print(f"⚠️ Error processing event: {e}")
                        # Add event with error info
                        events_with_timezone.append({
                            "title": event.get('summary', 'Event with parsing error'),
                            "start_time": "Time parsing error",
                            "date": "Unknown date",
                            "description": f"Error: {str(e)}",
                            "location": "",
                            "calendar_link": event.get('htmlLink', ''),
                            "event_id": event.get('id', '')
                        })
                
                return json.dumps({
                    "success": True,
                    "events": events_with_timezone,
                    "timezone_note": f"All times displayed in {self.timezone}",
                    "message": f"Found {len(events_with_timezone)} event(s) for {date_preference}",
                    "search_range": f"{start_date.strftime('%A, %B %d, %Y')} ({self.timezone})",
                    "calendar_url": "https://calendar.google.com"
                })
                
            except Exception as e:
                print(f"❌ Error in get_calendar_events: {e}")
                return json.dumps({
                    "success": False, 
                    "error": str(e),
                    "message": f"Error retrieving calendar events: {str(e)}"
                })
        @tool 
        def open_google_calendar(view: str = "week") -> str:
            """Generate Google Calendar URL with clickable link in message"""
            try:
                current = datetime.now(self.tz)
                
                # Generate calendar URL with current date
                base_url = "https://calendar.google.com/calendar/u/0/r"
                
                # Add view parameters
                view_params = {
                    'day': f'/day/{current.strftime("%Y/%m/%d")}',
                    'week': f'/week/{current.strftime("%Y/%m/%d")}',
                    'month': f'/month/{current.strftime("%Y/%m/%d")}',
                    'agenda': '/agenda'
                }
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": f"Error generating calendar link: {str(e)}"
                })
        @tool
        def verify_meeting_exists(meeting_title: str = "", date_preference: str = "tomorrow") -> str:
            """
            Verify if a specific meeting exists in the calendar.
            
            Args:
                meeting_title: Title of the meeting to search for
                date_preference: Date to search on
            
            Returns:
                JSON string with verification result
            """
            try:
                start_date, end_date = self._parse_smart_date(date_preference)
                
                # Convert to UTC for calendar service
                start_utc = start_date.astimezone(pytz.UTC)
                end_utc = end_date.astimezone(pytz.UTC)
                
                # Get events from calendar
                events_result = self.calendar_service.service.events().list(
                    calendarId='primary',
                    timeMin=start_utc.isoformat(),
                    timeMax=end_utc.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                # Search for matching meetings
                matching_events = []
                for event in events:
                    title = event.get('summary', '').lower()
                    if not meeting_title or meeting_title.lower() in title:
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        
                        if 'T' in start:  # DateTime format
                            event_start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                            event_start_local = event_start.astimezone(self.tz)
                            time_str = event_start_local.strftime('%I:%M %p')
                            date_str = event_start_local.strftime('%A, %B %d, %Y')
                        else:  # All-day event
                            date_str = datetime.fromisoformat(start).strftime('%A, %B %d, %Y')
                            time_str = "All day"
                        
                        matching_events.append({
                            "title": event.get('summary', 'No title'),
                            "date": date_str,
                            "time": time_str,
                            "id": event.get('id'),
                            "html_link": event.get('htmlLink', '')
                        })
                
                if matching_events:
                    return json.dumps({
                        "success": True,
                        "found": True,
                        "message": f"✅ Found {len(matching_events)} matching meeting(s) for '{meeting_title}' on {date_preference}",
                        "meetings": matching_events,
                        "calendar_url": "https://calendar.google.com"
                    })
                else:
                    return json.dumps({
                        "success": True,
                        "found": False,
                        "message": f"❌ No meetings found for '{meeting_title}' on {date_preference}",
                        "meetings": [],
                        "calendar_url": "https://calendar.google.com"
                    })
                    
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": f"Error verifying meeting: {str(e)}"
                })

        # Update the tools list in _create_tools method
        return [search_available_slots, book_meeting, get_current_time_info, change_timezone, 
                get_calendar_events, open_google_calendar, verify_meeting_exists]

    def _parse_smart_date(self, date_preference: str) -> tuple[datetime, datetime]:
        """Enhanced date parsing with support for specific dates like '29th June'"""
        date_preference = date_preference.lower().strip()
        now = self.current_time
        
        print(f"🔍 Parsing '{date_preference}' from current time: {now.strftime('%Y-%m-%d %I:%M %p %Z')}")
        
        target_date = now
        
        try:
            # Handle specific date patterns like "29th june", "june 29th", "29/6", etc.
            import re
            
            # Pattern for "29th June", "June 29th", "29 June"
            date_pattern = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', date_preference, re.IGNORECASE)
            
            if date_pattern:
                day = int(date_pattern.group(1))
                month_str = date_pattern.group(2).lower()
                
                # Month mapping
                month_map = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
                    'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                    'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                }
                
                month = month_map.get(month_str, now.month)
                year = now.year
                
                # If the date has passed this year, assume next year
                try:
                    target_date = now.replace(year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
                    if target_date < now:
                        target_date = target_date.replace(year=year + 1)
                except ValueError:
                    # Invalid date (like Feb 30th), fall back to next occurrence
                    target_date = now.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
                    if target_date < now:
                        target_date = target_date.replace(year=year + 1)
                
                start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
            elif "today" in date_preference:
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                
            elif "tomorrow" in date_preference:
                target_date = now + timedelta(days=1)
                start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
            elif "next week" in date_preference:
                target_date = now + timedelta(days=7)
                start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
            # Handle day names like "next friday", "monday"
            elif any(day in date_preference for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                for i, day_name in enumerate(day_names):
                    if day_name in date_preference:
                        current_weekday = now.weekday()
                        days_ahead = (i - current_weekday) % 7
                        
                        # If it's today and user says "monday" (and today is monday), assume next monday
                        if days_ahead == 0:
                            if "next" in date_preference:
                                days_ahead = 7
                            elif now.hour >= 17:  # After business hours, assume next occurrence
                                days_ahead = 7
                        
                        target_date = now + timedelta(days=days_ahead)
                        break
                
                start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
            else:
                # Default to today
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        except Exception as e:
            print(f"⚠️ Error parsing date preference '{date_preference}': {e}")
            # Fallback to today
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"📅 Parsed date range: {start_date.strftime('%Y-%m-%d %I:%M %p %Z')} to {end_date.strftime('%Y-%m-%d %I:%M %p %Z')}")
        
        return start_date, end_date

    def _create_agent(self):
        """Create the LLM agent with function calling"""
        
        system_prompt = f"""You are TailorTalk, an intelligent AI calendar assistant. You are helpful, friendly, and efficient at scheduling meetings.

CURRENT CONTEXT:
- Today is {self.current_time.strftime('%A, %B %d, %Y')}
- Current time: {self.current_time.strftime('%I:%M %p')} {self.timezone}
- Your timezone is set to: {self.timezone}

TIMEZONE SUPPORT:
- Available timezones: GMT, IST (India Standard Time), AST (Atlantic Standard Time)
- Always show times in the user's current timezone
- Use get_current_time_info() to check current time
- Use change_timezone() if user wants to switch timezones

PERSONALITY:
- Be conversational and natural
- Ask clarifying questions when needed
- Provide helpful suggestions
- Be proactive in offering alternatives
- Handle any type of query, not just scheduling

CAPABILITIES:
- Schedule meetings and appointments
- Check calendar availability  
- View existing calendar events and appointments
- Verify that meetings have been successfully booked
- Open Google Calendar for users
- Reschedule existing meetings
- Answer questions about calendar management
- Provide calendar summaries
- Handle casual conversation
- Give advice about meeting planning
- Switch between timezones

CALENDAR VIEWING TOOLS:
- get_calendar_events(): View events for specific dates
- open_google_calendar(): Generate calendar URL for user to open
- verify_meeting_exists(): Check if a specific meeting was booked

SLOT SEARCHING RULES:
- When user asks for "29th June" or specific dates, use search_available_slots with that exact phrase
- Always search for availability first before saying "no slots available"
- If no slots found, suggest alternative dates or times
- Show timezone information with all time displays

EXAMPLE USER QUERIES:
- "29th June 3-4 PM IST 1 hour meeting" → search_available_slots("29th June", 60)
- "Tomorrow afternoon" → search_available_slots("tomorrow", 60)
- "Next Friday morning" → search_available_slots("next Friday", 60)

AVAILABILITY CHECKING:
1. ALWAYS use search_available_slots first when user mentions dates
2. Parse duration from user input (default 60 minutes)
3. Show results with proper timezone conversion
4. If no slots found, suggest alternatives

NEVER assume no availability without checking the calendar first!

IMPORTANT GUIDELINES:
1. Always be helpful and try to understand user intent
2. When checking dates, use get_current_time_info() to ensure accuracy
3. If a user asks about scheduling, use the search_available_slots tool
4. When booking, confirm details before using book_meeting tool
5. Handle edge cases gracefully (no availability, past dates, etc.)
6. You can discuss topics beyond just calendar scheduling
7. Be conversational - don't force users into rigid flows
8. Remember context from the conversation
9. Offer multiple options when possible
10. Always mention the timezone when showing times

CONVERSATION STYLE:
- Natural and friendly tone
- Use emojis appropriately 
- Ask follow-up questions to clarify
- Summarize what you understand
- Confirm before taking actions
- Always be aware of the current date and time

MEETING VERIFICATION:
- After booking a meeting, you can verify it exists using verify_meeting_exists
- Offer to show the user their calendar with open_google_calendar
- Use get_calendar_events to show what's scheduled

Remember: Today is {self.current_time.strftime('%A, %B %d, %Y')} in {self.timezone}. Use this as your reference point for all date calculations.
TIMEZONE DISPLAY RULES:
- ALWAYS show times with timezone abbreviation: "2:00 PM (IST)", "10:00 AM (GMT)"
- When listing calendar events, format as: "Meeting - 11:00 AM - 12:00 PM (IST)"
- Current timezone: {self.timezone}
- Current time: {self.current_time.strftime('%I:%M %p')} ({self.timezone})

CALENDAR LINK FORMATTING:
When providing Google Calendar links, ALWAYS include the full URL in your message text like this:
✅ "Here's your Google Calendar link: https://calendar.google.com/calendar/u/0/r/day/2025/06/27"
✅ "Click here to open your calendar: https://calendar.google.com/calendar/u/0/r/week/2025/06/27"

NEVER just return JSON - always include the clickable URL in the message text!

TIME FORMAT RULES:
- ALWAYS use 12-hour AM/PM format: "4:00 PM (IST)", "10:30 AM (GMT)"
- Include timezone abbreviation in parentheses
- When showing events: "Meeting - 4:00 PM - 5:00 PM (IST)"

EXAMPLE RESPONSES:
✅ "Here's your Google Calendar link: https://calendar.google.com/calendar/u/0/r/day/2025/06/27

You can view your scheduled appointments for today, June 27, 2025."

Always include the full URL directly in your response text!

Remember to ALWAYS include ({self.timezone}) after every time you display!"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
    
    def process_message(self, user_input: str, state: Optional[SmartAgentState] = None) -> SmartAgentState:
        """Process user message with full LLM intelligence"""
        
        if state is None:
            state = {
                "conversation_history": [],
                "extracted_info": {},
                "available_slots": [],
                "session_context": {"timezone": self.timezone}
            }
        
        # Add user message to history
        state["conversation_history"].append({
            "role": "user",
            "content": user_input
        })
        
        # Prepare chat history for the agent
        chat_history = []
        for msg in state["conversation_history"]:
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            else:
                chat_history.append(AIMessage(content=msg["content"]))
        
        try:
            # Let the LLM agent handle the conversation intelligently
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history[:-1]  # Don't include the current message
            })
            
            assistant_message = response["output"]
            
            # Add assistant response to history
            state["conversation_history"].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Update session context
            state["session_context"]["timezone"] = self.timezone
            state["session_context"]["last_update"] = self.current_time.isoformat()
            
        except Exception as e:
            error_message = f"I apologize, but I encountered an error: {str(e)}. Please try again or rephrase your request."
            state["conversation_history"].append({
                "role": "assistant",
                "content": error_message
            })
        
        return state