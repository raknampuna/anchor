from datetime import datetime
from typing import Optional
import urllib.parse
from dataclasses import dataclass

@dataclass
class EventDetails:
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None

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
        if event.end_time <= event.start_time:
            raise ValueError("End time must be after start time")

        params = {
            'action': 'TEMPLATE',
            'text': event.title,
            'details': event.description,
            'dates': f"{self._format_datetime(event.start_time)}/{self._format_datetime(event.end_time)}"
        }
        
        if event.location:
            params['location'] = event.location

        return f"{self.base_url}?{urllib.parse.urlencode(params)}"