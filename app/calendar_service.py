from datetime import datetime
from typing import Optional, List
import urllib.parse
from pydantic import BaseModel, validator
from zoneinfo import ZoneInfo

class TimeBlock(BaseModel):
    """Time block for scheduling"""
    start_time: str      # Start time in HH:MM format
    end_time: str       # End time in HH:MM format
    description: str    # Description of the time block
    is_focus_block: bool # Whether this is a focus block for the main task

class EventDetails(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    timezone: str = "UTC"  # Default to UTC if not specified
    constraints: List[TimeBlock] = []

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

    @validator('timezone')
    def timezone_must_be_valid(cls, v):
        try:
            ZoneInfo(v)
            return v
        except Exception:
            raise ValueError(f'Invalid timezone: {v}')

    def check_constraints(self) -> bool:
        """Check if event conflicts with any constraints"""
        event_start = self.start_time.time()
        event_end = self.end_time.time()
        
        for block in self.constraints:
            block_start = datetime.strptime(block.start_time, "%H:%M").time()
            block_end = datetime.strptime(block.end_time, "%H:%M").time()
            
            if (block_start <= event_start <= block_end or 
                block_start <= event_end <= block_end):
                if not block.is_focus_block:
                    return False
        return True

class CalendarLinkService:
    def __init__(self):
        self.base_url = "https://calendar.google.com/calendar/render"

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for Google Calendar URL with timezone handling"""
        if dt.tzinfo is None:
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y%m%dT%H%M%SZ")

    def create_calendar_link(self, event: EventDetails) -> str:
        """Generate Google Calendar URL with event details"""
        if not event.check_constraints():
            raise ValueError("Event conflicts with existing constraints")

        params = {
            'action': 'TEMPLATE',
            'text': event.title,
            'details': event.description,
            'dates': f"{self._format_datetime(event.start_time)}/{self._format_datetime(event.end_time)}"
        }
        
        if event.location:
            params['location'] = event.location

        return f"{self.base_url}?{urllib.parse.urlencode(params)}"