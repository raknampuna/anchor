# Technical Specifications

## Component Architecture

### 1. LLM Service (`app/llm.py`)

#### Overview
Natural language processing service using Google's Gemini model for task extraction, scheduling suggestions, and response generation. Focuses on immediate task scheduling without maintaining complex state.

#### Conversation States
```python
class ConversationState:
    INIT = "init"
    GETTING_CONSTRAINTS = "getting_constraints"
    GETTING_DURATION = "getting_duration"
    CONFIRMING_SCHEDULE = "confirming_schedule"
    REPLANNING = "replanning"
    REFLECTION = "reflection"
```

#### Key Functions
- `process_message(message, state, context)`: Main entry point for message processing
- `suggest_time_block(task_info)`: Generate time block suggestions
- `generate_planning_prompt()`: Morning planning messages
- `generate_reflection_prompt(task)`: Evening reflection messages

#### Internal Functions
- `_extract_task_info()`: Initial task and constraint extraction
- `_extract_constraints()`: Additional constraint extraction
- `_extract_duration()`: Task duration parsing
- `_extract_time()`: Time parsing for replanning
- `_analyze_completion()`: Task completion analysis

### 2. Storage Service (`app/storage.py`)

#### Redis Schema
```python
{
    "user_id:YYYYMMDD": {
        "state": str,  # Current conversation state
        "task_info": {
            "task": str,
            "duration_minutes": int,
            "deadline": str,
            "constraints": List[str]
        },
        "time_block": {
            "start_time": str,
            "end_time": str
        },
        "completion": {
            "completed": bool,
            "follow_up": str
        }
    }
}
```

#### Key Functions
- `get_context(user_id)`: Retrieve user's daily context
- `update_context(user_id, context)`: Update context
- `cleanup_expired()`: Midnight cleanup

### 3. Scheduler Service (`app/scheduler.py`)

#### Cron Jobs
- 7am PT: Morning planning prompt
- 8pm PT: Evening reflection prompt
- 12am PT: Context cleanup

#### Retry Logic
- Max 3 retries for SMS sending
- Exponential backoff
- Error logging

### 4. Calendar Service (`app/calendar_service.py`)
Existing implementation, no changes needed.

## System Flows

### 1. Morning Planning (7am)
```
Cron Job (scheduler.py) 
→ Triggers planning prompt
→ LLMService.generate_planning_prompt()
→ SMS sent via routes.py

User replies with task
→ routes.py webhook receives message
→ LLMService.process_message(msg, state=INIT)
   - Calls _extract_task_info() internally
   - Returns response asking for constraints
   - State saved in Redis (storage.py)

User replies with constraints
→ LLMService.process_message(msg, state=GETTING_CONSTRAINTS)
   - Calls _extract_constraints() internally
   - Updates context in Redis
   - Moves to duration question

User provides duration
→ LLMService.process_message(msg, state=GETTING_DURATION)
   - Calls _extract_duration()
   - Calls suggest_time_block()
   - CalendarService.create_calendar_link()
   - Final response with calendar link
```

### 2. Mid-day Replanning
```
User sends "replan" message
→ routes.py webhook
→ Redis loads current task context
→ LLMService.process_message(msg, state=REPLANNING)
   - Uses existing task info from Redis
   - Asks for new availability

User provides availability
→ LLMService.process_message(msg, state=REPLANNING)
   - Calls _extract_time()
   - Calls suggest_time_block() with new constraints
   - CalendarService.create_calendar_link()
   - Updates task timing in Redis
```

### 3. Evening Reflection (8pm)
```
Cron Job 
→ Loads task from Redis
→ LLMService.generate_reflection_prompt(task)
→ SMS sent

User responds
→ LLMService.process_message(msg, state=REFLECTION)
   - Calls _analyze_completion()
   - Updates completion status in Redis
   - Optionally suggests tomorrow's task
```

## Configuration

### Required Settings (`config/settings.py`)
```python
# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Timezone
DEFAULT_TIMEZONE = "America/Los_Angeles"

# Cron Schedule (PT)
MORNING_PROMPT_TIME = "07:00"
EVENING_PROMPT_TIME = "20:00"
CONTEXT_CLEANUP_TIME = "00:00"

# Twilio Configuration
TWILIO_ACCOUNT_SID = "..."
TWILIO_AUTH_TOKEN = "..."
TWILIO_PHONE_NUMBER = "+1..."
```

## Error Handling

### SMS Errors
- Retry with exponential backoff
- User-friendly error messages
- Error logging without sensitive data

### LLM Errors
- Default responses for extraction failures
- Fallback to simple responses
- Error reporting for monitoring

### Redis Errors
- Connection retry logic
- Graceful degradation
- Error monitoring

## Testing Strategy

### Unit Tests
- LLM response validation
- Redis operations
- Schedule calculations

### Integration Tests
- End-to-end message flows
- Cron job execution
- Error scenarios

## Security Considerations

### Data Privacy
- Daily context cleanup at midnight
- Minimal user data storage
- Secure configuration management

### API Security
- Webhook authentication
- Rate limiting
- Minimal error exposure