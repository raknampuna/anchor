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

### 6. Logging System (`app/logging.py`)

#### Overview
Structured logging system that maintains both consolidated and type-specific logs for each phone number, enabling both easy manual review and programmatic analysis.

#### Directory Structure
```
logs/
  └── phone_numbers/
      └── +1234567890/
          ├── consolidated.log     # All events in chronological order
          └── by_type/            # Separated by concern
              ├── interaction.log  # User interactions
              ├── llm.log         # LLM requests/responses
              └── error.log       # Error events
```

#### Log Format
```json
{
  "timestamp": "2025-01-13T07:29:22-08:00",
  "level": "INFO",
  "event_type": "user_interaction|llm_response|error|system",
  "phone_number": "+1234567890",
  "data": {
    "duration_ms": 1234,          // Performance tracking
    "related_events": ["uuid-1"], // Links to related log entries
    "status": "success|failed",   // Event outcome
    "error_type": "rate_limit",   // For error categorization
    "message": "User message or error description",
    "component": "llm|storage|sms", // Source component
    // Event-specific data...
  },
  "metadata": {
    "session_id": "uuid",
    "version": "1.0",
    "trace_id": "uuid"  // For request tracing
  }
}
```

#### Event Types
- `user_interaction`: Messages received from or sent to users
- `llm_response`: Inputs to and outputs from the LLM service
- `error`: System errors and exceptions
- `system`: Internal system events (startup, shutdown, etc.)

#### CLI Tool (`logs.py`)
Command-line interface for log viewing and analysis:

```bash
# Basic Usage
./logs.py view PHONE_NUMBER    # View consolidated logs
./logs.py follow PHONE_NUMBER  # Follow logs in real-time

# Cross-Number Analysis
./logs.py search --all-numbers [options]  # Search across all numbers
./logs.py summary --all-numbers [options] # Statistics across all numbers

# Error Analysis
./logs.py search --all-numbers --level ERROR --context 5min
./logs.py search --error-type rate_limit
./logs.py summary --focus errors --last 7d

# Performance Analysis
./logs.py search --type llm --duration ">5000"  # Slow LLM responses
./logs.py summary --focus latency --component llm
./logs.py search --status failed --component storage

# User Interaction Analysis
./logs.py search --type interaction --contains "don't understand"
./logs.py summary --focus completion-rate
./logs.py search --pattern "rescheduling" --last 24h

# System Health
./logs.py search --type system --level WARNING|ERROR
./logs.py summary --focus "rate-limits,quotas" --last 1h

Options:
  --level LEVEL         Filter by log level (INFO|WARNING|ERROR)
  --since TIME         Show logs since time (e.g. "2h ago", "2025-01-13")
  --event-type TYPE    Filter by event type
  --context TIME       Show surrounding events within time window
  --component NAME     Filter by system component
  --status STATUS     Filter by event status
  --error-type TYPE   Filter by error category
  --duration EXPR     Filter by duration (e.g. ">5000", "<1000")
  --contains TEXT     Search in message content
  --pattern REGEX     Search using regex pattern
  --focus METRIC      Focus summary on specific metrics
```

#### Key Features
- Structured JSON logging for machine readability
- Consolidated and type-specific logs
- Cross-number analysis capabilities
- Performance tracking and monitoring
- Error correlation and analysis
- User interaction pattern analysis
- System health monitoring
- Flexible search and filtering
- Customizable summary statistics
- Colorized CLI output
- Unix pipe compatibility

#### Implementation Notes
- Uses Python's built-in logging module with custom formatters
- Automatic log rotation to manage file sizes
- Thread-safe writing to multiple log files
- Efficient disk usage through shared file handles
- Sanitized phone numbers for directory names
- UTC timestamps with timezone information
- Event correlation through related_events and trace_id
- Categorized error types for better analysis
- Component-level tracking for targeted debugging

#### Common Query Patterns
1. Error Investigation:
   ```bash
   # Find error and related events
   ./logs.py search --trace-id <id> --context 5min
   
   # Track error patterns
   ./logs.py summary --focus errors --group-by error_type
   ```

2. Performance Monitoring:
   ```bash
   # Component latency analysis
   ./logs.py summary --focus latency --group-by component
   
   # Slow operation detection
   ./logs.py search --duration ">5000" --last 1h
   ```

3. User Experience Analysis:
   ```bash
   # Completion rate tracking
   ./logs.py summary --focus completion-rate --group-by hour
   
   # Confusion point detection
   ./logs.py search --pattern "what|how|why" --type interaction
   ```

4. System Health:
   ```bash
   # Service disruption detection
   ./logs.py search --level ERROR --group-by component
   
   # Resource usage tracking
   ./logs.py summary --focus "rate-limits,quotas" --last 24h
   ```

#### Future Considerations
- Log aggregation across multiple instances
- Dashboard integration
- Advanced analytics and ML-based pattern detection
- Log retention policies
- Export capabilities
- Real-time alerting based on log patterns
- Custom metric definition and tracking

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