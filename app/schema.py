"""Schema definitions for Anchor task planning system."""

from typing import Optional, List
import json
from datetime import datetime, time
from pydantic import BaseModel, Field
from enum import Enum

class MessageType(str, Enum):
    """Types of interactions with the user"""
    MORNING_PLANNING = "morning_planning"
    REPLANNING = "replanning"
    EVENING_REFLECTION = "evening_reflection"
    AD_HOC = "ad_hoc"

class TimeBlock(BaseModel):
    """Time block for scheduling"""
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: Optional[str] = Field(None, description="End time in HH:MM format")
    description: Optional[str] = Field(None, description="Description of the time block")
    is_focus_block: bool = Field(default=False, description="Whether this is a focus block for the main task")

class TaskTiming(BaseModel):
    """Timing information for a task"""
    duration_minutes: Optional[int] = Field(None, description="Expected duration in minutes")
    deadline: Optional[str] = Field(None, description="Deadline time in HH:MM format")
    preferred_time: Optional[str] = Field(None, description="User's preferred time in HH:MM format")
    constraints: List[TimeBlock] = Field(default_factory=list, description="List of time constraints")

class LLMResponse(BaseModel):
    """Schema for LLM responses"""
    response: str = Field(..., description="Natural language response to user")
    task: Optional[str] = Field(None, description="Task description if provided")
    message_type: MessageType = Field(
        default=MessageType.AD_HOC,
        description="Message type for this interaction"
    )
    timing: Optional[TaskTiming] = Field(None, description="Timing information if provided")

    @classmethod
    def from_llm_output(cls, text: str) -> "LLMResponse":
        """Parse LLM output into structured response.
        
        The LLM output is expected in the format:
        RESPONSE: Natural language response
        INFO: {
            "task": string or null,
            "message_type": string,
            "timing": {...} or null
        }
        
        Uses a simple, stable parsing approach that:
        1. Finds the last occurrence of RESPONSE: and INFO: markers
        2. Extracts JSON from the INFO section
        3. Falls back to friendly defaults if parsing fails
        """
        try:
            # Find the last occurrence of RESPONSE: and INFO: 
            # (in case they appear in the example part of the prompt)
            response_idx = text.rfind("RESPONSE:")
            info_idx = text.rfind("INFO:")
            
            if response_idx == -1 or info_idx == -1:
                raise ValueError("Missing RESPONSE or INFO section")
                
            # Extract the response text
            response_text = text[response_idx + 9:info_idx].strip()
            
            # Extract and parse the JSON part
            info_text = text[info_idx + 5:].strip()
            info = json.loads(info_text)
            
            # Create response with simple defaults if parts are missing
            return cls(
                response=response_text,
                task=info.get("task"),
                message_type=MessageType(info.get("message_type", "ad_hoc")),
                timing=TaskTiming(**info["timing"]) if info.get("timing") else None
            )
            
        except Exception as e:
            print(f"Error parsing LLM output: {str(e)}")
            print(f"Raw output: {text}")
            return cls(
                response="Hi! I'm here to help you plan your tasks. What would you like to accomplish today?",
                task=None,
                message_type=MessageType.AD_HOC,
                timing=None
            )