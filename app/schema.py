"""Schema definitions for Anchor task planning system."""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, time
from enum import Enum

class MessageType(str, Enum):
    """Types of interactions with the user"""
    MORNING_PLANNING = "morning_planning"
    REPLANNING = "replanning"
    EVENING_REFLECTION = "evening_reflection"
    AD_HOC = "ad_hoc"

class TimeBlock(BaseModel):
    """Schema for time block suggestions"""
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    calendar_link: Optional[str] = Field(None, description="Generated calendar link")

class TaskCompletion(BaseModel):
    """Schema for evening reflection data"""
    completed: bool = Field(..., description="Whether the task was completed")
    follow_up_task: Optional[str] = Field(None, description="Follow-up task for tomorrow")
    learnings: Optional[str] = Field(None, description="Key learnings or blockers")

class TaskInfo(BaseModel):
    """Schema for task information extracted from messages"""
    task: Optional[str] = Field(None, description="The main task description")
    duration_minutes: Optional[int] = Field(None, description="Task duration in minutes")
    constraints: List[str] = Field(default_factory=list, description="List of time constraints")
    time_block: Optional[TimeBlock] = Field(None, description="Suggested time block")
    completion: Optional[TaskCompletion] = Field(None, description="Task completion info")

class UserContext(BaseModel):
    """Schema for user context"""
    timezone: Optional[str] = Field(None, description="User's timezone")
    last_interaction: Optional[datetime] = Field(None, description="Last message timestamp")
    current_task: Optional[TaskInfo] = Field(None, description="Current task info")
    message_type: MessageType = Field(default=MessageType.AD_HOC, description="Type of interaction")

class LLMResponse(BaseModel):
    """Schema for LLM responses"""
    response: str = Field(..., description="Natural language response to user")
    info: TaskInfo = Field(..., description="Structured task information")
    suggested_message_type: MessageType = Field(
        default=MessageType.AD_HOC,
        description="Suggested next interaction type"
    )

    @classmethod
    def from_llm_output(cls, text: str) -> "LLMResponse":
        """Parse LLM output into structured response"""
        try:
            # Split response and info sections
            response_parts = text.split('INFO:', 1)
            if len(response_parts) != 2:
                raise ValueError("Response missing INFO section")
                
            response_text = response_parts[0].replace('RESPONSE:', '').strip()
            info_json = response_parts[1].strip()
            
            return cls(
                response=response_text,
                info=TaskInfo.model_validate_json(info_json)
            )
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

    def update_context(self, context: UserContext) -> UserContext:
        """Update user context with new information"""
        if self.info.task:
            context.current_task = self.info
        
        context.message_type = self.suggested_message_type
        context.last_interaction = datetime.now()
        
        return context