"""
TailorTalk Models Package
Contains all data models for the calendar booking system
"""
from .calendar_model import (
    MeetingType,
    TimeSlot,
    BookingRequest,
    BookingResponse,
    ConversationState
)

__all__ = [
    "MeetingType",
    "TimeSlot",
    "BookingRequest", 
    "BookingResponse",
    "ConversationState"
]