from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class MeetingType(str, Enum):
    CALL = "call"
    MEETING = "meeting"
    CONSULTATION = "consultation"
    INTERVIEW = "interview"
    FOLLOW_UP = "follow_up"

class TimeSlot(BaseModel):
    start: datetime
    end: datetime
    duration_minutes: int
    available: bool = True
    
class BookingRequest(BaseModel):
    title: str
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    duration_minutes: int = Field(default=60, ge=15, le=480)
    meeting_type: MeetingType = MeetingType.MEETING
    description: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    
class BookingResponse(BaseModel):
    success: bool
    event_id: Optional[str] = None
    message: str
    suggested_slots: List[TimeSlot] = Field(default_factory=list)
    
class ConversationState(BaseModel):
    user_id: str
    current_step: str = "greeting"
    extracted_info: BookingRequest = Field(default_factory=BookingRequest)
    conversation_history: List[dict] = Field(default_factory=list)
    last_suggested_slots: List[TimeSlot] = Field(default_factory=list)
    