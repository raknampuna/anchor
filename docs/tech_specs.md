# Technical Specifications

## Component Architecture

### 1. LLM Service (`app/llm.py`)

#### Overview
Natural language processing service using Google's Gemini model for task extraction, scheduling suggestions, and response generation. Focuses on immediate task scheduling without maintaining complex state.

#### Response Processing
The service uses a simple, stable approach to process LLM outputs:
```python
# Expected Format
RESPONSE: Natural language response to user
INFO: {
    "task": string or null,
    "message_type": string,
    "timing": {...} or null
}
```

Key design decisions:
- Simple marker-based parsing (RESPONSE: and INFO:)
- Uses last occurrence of markers to handle example text
- Graceful fallbacks for parsing failures
- Structured logging for debugging

#### Key Functions
- `process_message(user_id, message, message_type) -> LLMResponse`: Main entry point for message processing, returns structured response
- `LLMResponse.from_llm_output(text) -> LLMResponse`: Parse LLM output into structured data

#### Error Handling
- All LLM interactions return valid `LLMResponse` objects
- Failed parsing defaults to AD_HOC message type
- Maintains conversation flow even during errors
- User-friendly error messages that encourage task focus

#### Response Format
```python
LLMResponse:
    response: str          # Natural language response
    task: Optional[str]    # Extracted task
    message_type: MessageType
    timing: Optional[TaskTiming]
```

#### Message Types
```python
class MessageType:
    MORNING_PLANNING = "morning_planning"  # Help identify and schedule day's task
    REPLANNING = "replanning"             # Adjust schedule based on changes
    EVENING_REFLECTION = "reflection"      # Simple end-of-day check-in
    AD_HOC = "ad_hoc"                     # Handle general inquiries
```

### 2. Storage Service (`app/storage.py`)

#### Overview
Simple Redis-based storage for maintaining minimal daily context. Focuses on storing only essential user data needed for daily interactions.

#### Data Models
```python
class TimeBlock:
    """Time block for scheduling"""
    start_time: str      # Start time in HH:MM format
    end_time: str       # End time in HH:MM format
    description: str    # Description of the time block
    is_focus_block: bool # Whether this is a focus block for the main task

class TaskTiming:
    """Timing information for a task"""
    duration_minutes: int    # Expected duration in minutes
    deadline: str           # Deadline time in HH:MM format
    preferred_time: str     # User's preferred time in HH:MM format
    constraints: List[TimeBlock] # List of time constraints
```

#### Redis Schema
```python
{
    "user_id:YYYYMMDD": {
        "message_type": str,      # Current message type
        "current_task": str,      # The task description
        "timing": {              # Task timing information
            "duration_minutes": int,
            "deadline": str,
            "preferred_time": str,
            "constraints": [
                {
                    "start_time": str,
                    "end_time": str,
                    "description": str,
                    "is_focus_block": bool
                }
            ]
        },
        "last_interaction": str,  # Timestamp of last interaction
    }
}
```

#### Key Functions
- `save_context(user_id, context)`: Store daily user context
- `get_context(user_id)`: Retrieve current day's context
- `cleanup_old_contexts(days=7)`: Remove contexts older than specified days

### 3. Calendar Service (`app/calendar_service.py`)

#### Overview
Handles calendar link generation for task scheduling. Uses existing implementation.

### 4. Routes (`app/routes.py`)

#### Core Flows
```
Morning Planning:
SMS → Extract Task → Suggest Time → Calendar Link → Response

Mid-day Replanning:
SMS → Load Context → Suggest New Time → Calendar Link → Response

Evening Reflection:
SMS → Load Context → Update Completion → Response
```

### 5. Scheduler (`app/scheduler.py`)

#### Overview
Manages daily triggers for morning planning and evening reflection prompts.

#### Schedule
- 7am PT: Morning planning prompt
- 8pm PT: Evening reflection prompt
- 12am PT: Context cleanup

## Configuration (`config/settings.py`)

### Key Settings
- Redis connection details
- Default timezone (PT)
- Context cleanup period
- Environment variables management

## Security Considerations

### Data Storage
- Minimal user data storage
- Daily context cleanup
- No sensitive data storage

### API Security
- Webhook authentication
- Environment variable protection