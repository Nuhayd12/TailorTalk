from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime, timedelta
import re
import json
from enum import Enum

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Import our calendar service
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from cal_service import GoogleCalendarService

class ConversationStep(str, Enum):
    GREETING = "greeting"
    INTENT_RECOGNITION = "intent_recognition"
    DATE_EXTRACTION = "date_extraction"
    TIME_PREFERENCE = "time_preference"
    DURATION_CONFIRMATION = "duration_confirmation"
    AVAILABILITY_CHECK = "availability_check"
    SLOT_SELECTION = "slot_selection"
    FINAL_CONFIRMATION = "final_confirmation"
    BOOKING_CREATION = "booking_creation"
    COMPLETION = "completion"

class AgentState(TypedDict):
    """State management for conversation flow"""
    conversation_history: List[Dict[str, str]]
    current_step: str
    user_input: str
    extracted_info: Dict[str, Any]
    available_slots: List[Dict[str, Any]]
    selected_slot: Optional[Dict[str, Any]]
    error_message: Optional[str]
    needs_clarification: bool
    waiting_for_user: bool

class TailorTalkAgent:
    """
    Intelligent conversational agent for calendar booking
    """
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o-mini",
            temperature=0.7
        )
        self.calendar_service = GoogleCalendarService()
        
        # Find credentials file in root directory
        root_credentials = os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json')
        if os.path.exists(root_credentials):
            self.calendar_service.authenticate(root_credentials)
        else:
            self.calendar_service.authenticate()  # Try default location
    
    def _parse_date_preference(self, user_input: str) -> tuple[datetime, datetime]:
        """Parse user's date preference and return start/end dates for search"""
        user_input = user_input.lower()
        now = datetime.now()
        
        # Handle "tomorrow"
        if "tomorrow" in user_input:
            target_date = now + timedelta(days=1)
            start_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
            end_date = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
            return start_date, end_date
        
        # Handle "today"
        if "today" in user_input:
            target_date = now
            start_date = max(now, target_date.replace(hour=9, minute=0, second=0, microsecond=0))
            end_date = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
            return start_date, end_date
        
        # Handle day names (Monday, Tuesday, etc.)
        days_of_week = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name, day_num in days_of_week.items():
            if day_name in user_input:
                # Find next occurrence of this day
                days_ahead = day_num - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                
                target_date = now + timedelta(days=days_ahead)
                start_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
                return start_date, end_date
        
        # Handle "next week"
        if "next week" in user_input:
            start_date = now + timedelta(days=7)
            end_date = start_date + timedelta(days=5)  # Monday to Friday of next week
            return start_date, end_date
        
        # Handle "this week"
        if "this week" in user_input or "week" in user_input:
            # Start from tomorrow if today is already late
            if now.hour >= 17:
                start_date = now + timedelta(days=1)
            else:
                start_date = now
            end_date = start_date + timedelta(days=5)
            return start_date, end_date
        
        # Default: search next 7 days
        start_date = now
        end_date = now + timedelta(days=7)
        return start_date, end_date
    
    def process_message(self, user_input: str, state: Optional[AgentState] = None) -> AgentState:
        """Process a single user message and return the response"""
        
        # Initialize state if first message
        if state is None:
            state = {
                "conversation_history": [],
                "current_step": "greeting",
                "user_input": user_input,
                "extracted_info": {"title": "Meeting", "duration_minutes": 60},
                "available_slots": [],
                "selected_slot": None,
                "error_message": None,
                "needs_clarification": False,
                "waiting_for_user": False
            }
            
            # First interaction - return greeting
            response = "Hello! I'm TailorTalk, your personal scheduling assistant. How can I help you book an appointment today?"
            state["conversation_history"] = [{
                "role": "assistant",
                "content": response
            }]
            state["current_step"] = "greeting"
            state["waiting_for_user"] = True
            return state
        
        # Update user input
        state["user_input"] = user_input
        
        # Add user message to history
        state["conversation_history"].append({
            "role": "user",
            "content": user_input
        })
        
        # Process based on current step
        if state["current_step"] == "greeting":
            return self._handle_intent_recognition(state)
        elif state["current_step"] == "intent_recognition":
            return self._handle_date_extraction(state)
        elif state["current_step"] == "date_extraction":
            return self._handle_availability_check(state)
        elif state["current_step"] == "availability_check":
            return self._handle_slot_selection(state)
        elif state["current_step"] == "slot_selection":
            return self._handle_final_confirmation(state)
        elif state["current_step"] == "final_confirmation":
            return self._handle_booking_creation(state)
        elif state["current_step"] == "completion":
            return self._handle_completion(state)
        elif state["current_step"] == "ended":
            # Conversation has ended, return a final message
            response = "This conversation has ended. Feel free to start a new chat anytime! 👋"
            state["conversation_history"].append({
                "role": "assistant",
                "content": response
            })
            return state
        else:
            return self._handle_completion(state)
    def _handle_intent_recognition(self, state: AgentState) -> AgentState:
        """Handle initial intent recognition"""
        response = "Great! I'd be happy to help you schedule that meeting. What date works best for you? You can say something like 'tomorrow', 'next Friday', or give me a specific date."
        
        state["conversation_history"].append({
            "role": "assistant",
            "content": response
        })
        state["current_step"] = "intent_recognition"
        state["waiting_for_user"] = True
        return state
    
    def _handle_date_extraction(self, state: AgentState) -> AgentState:
        """Handle date extraction and move to availability check"""
        # Store the date preference in extracted_info
        state["extracted_info"]["date_preference"] = state["user_input"]
        return self._handle_availability_check(state)
    
    def _handle_availability_check(self, state: AgentState) -> AgentState:
        """Check availability and show slots based on user's date preference"""
        
        # Get date preference from either current input or stored preference
        date_input = state.get("user_input", "")
        if not date_input and state["extracted_info"].get("date_preference"):
            date_input = state["extracted_info"]["date_preference"]
        
        # Parse the date preference
        start_date, end_date = self._parse_date_preference(date_input)
        
        try:
            free_slots = self.calendar_service.find_free_slots(
                start_date, 
                end_date, 
                duration_minutes=60
            )
            
            state["available_slots"] = free_slots[:5]
            
            if free_slots:
                # Show which day we're searching for
                date_context = ""
                if "friday" in date_input.lower():
                    date_context = " for Friday"
                elif "tomorrow" in date_input.lower():
                    date_context = " for tomorrow"
                elif any(day in date_input.lower() for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'saturday', 'sunday']):
                    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'saturday', 'sunday']:
                        if day in date_input.lower():
                            date_context = f" for {day.title()}"
                            break
                
                slots_text = "\n".join([
                    f"{i+1}. {datetime.fromisoformat(slot['start']).strftime('%A, %B %d at %I:%M %p')}"
                    for i, slot in enumerate(free_slots[:5])
                ])
                
                response = f"I found several available times{date_context}:\n\n{slots_text}\n\nWhich one works best for you? Just say the number (1, 2, 3, etc.)."
            else:
                response = f"I couldn't find any available slots for {date_input}. Would you like me to check a different day or time period?"
            
        except Exception as e:
            response = f"I had trouble checking your calendar for {date_input}. Let me try a different approach. When would you prefer to meet?"
            state["error_message"] = str(e)
        
        state["conversation_history"].append({
            "role": "assistant",
            "content": response
        })
        state["current_step"] = "availability_check"
        state["waiting_for_user"] = True
        return state
    def _handle_slot_selection(self, state: AgentState) -> AgentState:
        """Handle slot selection"""
        user_input = state.get("user_input", "").lower()
        available_slots = state.get("available_slots", [])
        
        # Try to extract slot number
        selected_index = None
        for i in range(1, 6):
            if str(i) in user_input or f"slot {i}" in user_input:
                selected_index = i - 1
                break
        
        if selected_index is not None and selected_index < len(available_slots):
            selected_slot = available_slots[selected_index]
            state["selected_slot"] = selected_slot
            
            time_str = datetime.fromisoformat(selected_slot['start']).strftime('%A, %B %d at %I:%M %p')
            response = f"Perfect! I'll book your meeting for {time_str}. Should I go ahead and create this appointment? (Just say 'yes' to confirm)"
            state["current_step"] = "slot_selection"
            
            # Clear available slots after selection
            state["available_slots"] = []
            
        else:
            response = "Please let me know which time slot you'd prefer by saying the number (1, 2, 3, etc.)."
            state["current_step"] = "availability_check"  # Stay in slot selection
        
        state["conversation_history"].append({
            "role": "assistant",
            "content": response
        })
        state["waiting_for_user"] = True
        return state

    def _handle_final_confirmation(self, state: AgentState) -> AgentState:
        """Handle final confirmation"""
        user_input = state.get("user_input", "").lower()
        
        if any(word in user_input for word in ["yes", "confirm", "book", "schedule", "okay", "ok"]):
            return self._handle_booking_creation(state)
        else:
            response = "No problem! Is there anything else I can help you with for your calendar?"
            state["conversation_history"].append({
                "role": "assistant", 
                "content": response
            })
            state["current_step"] = "completion"
            state["waiting_for_user"] = True
            return state
    
    def _handle_booking_creation(self, state: AgentState) -> AgentState:
        """Create the booking"""
        selected_slot = state.get("selected_slot")
        
        if selected_slot:
            try:
                start_time = datetime.fromisoformat(selected_slot['start'])
                end_time = datetime.fromisoformat(selected_slot['end'])
                
                event_id = self.calendar_service.create_event(
                    title="Meeting",
                    start_time=start_time,
                    end_time=end_time,
                    description="Scheduled via TailorTalk"
                )
                
                if event_id:
                    response = "🎉 Perfect! Your meeting has been successfully booked. You'll receive a calendar invitation shortly."
                else:
                    response = "I encountered an issue creating the calendar event. Please try again."
                    
            except Exception as e:
                response = f"Sorry, there was an error booking your meeting: {str(e)}"
        else:
            response = "There was an issue with the selected time slot. Please try again."
        
        state["conversation_history"].append({
            "role": "assistant",
            "content": response
        })
        state["current_step"] = "completion"
        state["waiting_for_user"] = False
        return state
    
    def _handle_completion(self, state: AgentState) -> AgentState:
        """Handle completion - either end conversation or start new booking"""
        user_input = state.get("user_input", "").lower()
        
        # Check if user wants to book another meeting
        booking_keywords = [
            "book", "schedule", "meeting", "appointment", "another", 
            "more", "again", "new", "yes", "today", "tomorrow",
            "monday", "tuesday", "wednesday", "thursday", "friday"
        ]
        
        # If user wants to book another meeting, restart the process
        if any(keyword in user_input for keyword in booking_keywords):
            response = "Great! I'd be happy to help you schedule another meeting. What date works best for you?"
            
            state["conversation_history"].append({
                "role": "assistant",
                "content": response
            })
            
            # Reset state for new booking
            state["current_step"] = "intent_recognition"
            state["extracted_info"] = {"title": "Meeting", "duration_minutes": 60}
            state["available_slots"] = []
            state["selected_slot"] = None
            state["error_message"] = None
            state["needs_clarification"] = False
            state["waiting_for_user"] = True
            
            return state
        
        # Check if user is saying goodbye
        goodbye_keywords = ["bye", "goodbye", "thanks", "thank you", "no", "nothing", "done", "exit", "quit"]
        
        if any(keyword in user_input for keyword in goodbye_keywords):
            response = "You're welcome! Have a great day and I look forward to helping you with your calendar again soon! 👋"
            
            state["conversation_history"].append({
                "role": "assistant",
                "content": response
            })
            state["current_step"] = "ended"
            state["waiting_for_user"] = False
            return state
        
        # Default response for unclear input
        response = "I can help you:\n• Schedule another meeting\n• Check your availability\n• Or if you're all set, just say 'thanks' or 'goodbye'!\n\nWhat would you like to do?"
        
        state["conversation_history"].append({
            "role": "assistant",
            "content": response
        })
        state["current_step"] = "completion"
        state["waiting_for_user"] = True
        return state