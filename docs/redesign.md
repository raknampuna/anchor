# AI-Powered Day Planner: System Redesign to "Anchor: Get It Done" MVP

## 1. Overview
This document outlines a focused MVP design for Anchor, a messaging-based chatbot that helps users identify and schedule their most important daily task. The system operates on a flexible interaction model, allowing users to respond throughout the day while maintaining a daily planning and reflection rhythm. It emphasizes natural conversation while avoiding complexity in favor of immediate utility.

### Design Principles
- **Do One Thing Well**: Focus solely on helping users identify and schedule their most important daily task, resisting the temptation to add features for edge cases
- **Embrace Simplicity**: Prefer direct message-based interaction over complex interfaces or workflows
- **Minimal Conversation History**: Daily conversation context only, with minimal persistent storage for essential user data
- **Immediate Value**: Prioritize immediate task scheduling over "smart" features that require historical data or learning
- **Trust the User**: Help users make scheduling decisions rather than trying to make decisions for them


## 2. System Design Summary

### Key Features
- **Morning Planning**: Help users identify and schedule their most important daily task (anchor task) through guided conversation
- **Smart Scheduling**: Extract user-provided scheduling constraints through natural language and suggest appropriate time blocks
- **Evening Reflection**: Simple end-of-day check-in to capture task completion, any learnings, and prompt to start planning for the next day
- **Flexible Interaction**: Handle ad-hoc user messages throughout the day while maintaining daily planning and reflection rhythm, including mid-day replanning when circumstances change
- **Graceful Recovery**: Simple error handling with clear user communication
- **Quick Start**: One-message signup with timezone capture and simple tutorial

### Key Interactions
1. Daily Planning (initiated at 7am local time):
Cron → LLM Planning → SMS → User Reply → Calendar Link → SMS

2. Daily Reflection (initiated at 8pm local time):
Cron → LLM Reflection → SMS → User Reply

3. Quick Start Flow:
Initial SMS → Capture Timezone → Welcome Tutorial → Planning Flow

4. Ad-hoc Interactions:
User SMS → Context Load → LLM Response → SMS
(includes replanning when schedule changes)

Each step:
1. Daily prompts at consistent times in user's timezone
2. Load today's context if exists
3. LLM generates appropriate message
4. User responds at their convenience
5. System processes response and updates context
6. Context refreshes daily at midnight

### Technical Stack
- Flask for web server and API endpoints
  - Simple and lightweight web framework
  - Blueprint-based route organization
  - Handles scheduled and ad-hoc interactions
  - CLI interface for testing
- LLM API for natural language processing and context understanding
- Google Calendar API for calendar link generation
- Redis for temporary context storage:
  - Today's anchor task (description, scheduled time)
  - Today's schedule (meetings and focus block)
  - Today's conversation state
- SQLite/PostgreSQL for persistent storage:
  - User accounts and phone numbers
  - Timezone preferences
  - Authentication data
- Cron job for daily prompts
- Twilio for SMS integration
- Basic error logging:
  - Simple console logging for development
  - Critical error alerts via email
  - Focus on user-facing error recovery
- Development interface:
  - CLI chat command for quick testing
  - Mirrors SMS conversation flow for rapid development

### User Privacy & Security
- Context refreshes daily at midnight
- Phone numbers stored with timezone only
- Error logs stripped of sensitive data
- Simple structure for easy maintenance

## 3. System Requirements

### User Experience Requirements
- **Task Management**
  - Clear task identification prompts
  - Duration estimation guidance
  - Time-block suggestions based on user-provided constraints
  - Replanning assistance

- **Interaction Design**
  - Simple yes/no confirmations when possible
  - Clear error messages and recovery options
  - Proactive schedule suggestions
  - Encouraging, supportive tone

### Key User Journeys

- **Morning Planning**
  - Task and schedule understanding
    > **Assistant**: "Good morning Sarah! What's your most important task for today?"

    > **Sarah**: "I need to finish the Q1 roadmap presentation for the product review at 2 PM."

    >**Assistant**: "I see you mentioned a 2 PM review. Any other time constraints I should consider for scheduling your presentation work?"

    > **Sarah**: "Just a quick standup at 11 AM."

  - Direct scheduling
    > **Assistant**: "How long do you need for the presentation?"

    > **Sarah**: "About 2 hours."

    > **Assistant**: "I'll create a 2-hour focus block at 8:30 AM. Here's your calendar link: https://calendar.google.com/..."

    > **Sarah**: "Perfect!"

- **Mid-day Replanning**
  - Handling schedule changes
    > **Sarah**: "Hey, an urgent customer issue came up and I couldn't work on the presentation this morning. Can we replan?"

    > **Assistant**: "Of course! You have the product review at 2 PM. What's your availability for the rest of the day?"

    > **Sarah**: "The customer issue should be resolved by 12:30 PM."

    > **Assistant**: "I can schedule a 90-minute focus block from 12:30 PM to 2 PM for your presentation. It's tight but doable. Would that work?"

    > **Sarah**: "Yes, that's perfect."

    > **Assistant**: "Great, I've updated your calendar. Here's the new event link: https://calendar.google.com/..."

- **Evening Check-in**
  - Simple reflection
    > **Assistant**: "Hi Sarah! How did today's presentation work go?"
    
    > **Sarah**: "Completed it, but the gantt chart section needs work."
    
    > **Assistant**: "Thanks for the update. Would you like to make the gantt chart your anchor task when we plan tomorrow morning?"
    
    > **Sarah**: "Yes, that would be good."

- **Quick Start**
  - Timezone capture and welcome
    > **Assistant**: "Welcome to Anchor! I'm here to help you get yourself organized. I do this by helping you to focus and accomplish the most important tasks of the day.  I currently reset every night to keep things simple, so I can only help you plan tasks for today. However, I'm always evolving, so always feel free to tell me what I can do better. To start, what timezone are you in?"
    
    > **User**: "Pacific time"
    
    > **Assistant**: "Great! I'll send you planning messages at 7am PT and reflection check-ins at 8pm PT."

  - Immediate first planning
    > **Assistant**: "Let's start planning your day now. What's your most important task for today?"
    
    > **User**: "I need to prepare for the quarterly review meeting."
    
    > **Assistant**: "When is the quarterly review meeting?"
    
    > **User**: "Today at 3 PM."
    
    > **Assistant**: "How much time do you need to prepare?"

### Core Functionality Requirements
- **Task Processing**
  - Extract task details from natural conversation
  - Extract time constraints and deadlines from user interaction
  - Handle schedule changes and replanning requests
  - Generate appropriate time block suggestions

- **Schedule Management**
  - Create calendar events
  - Handle timezone conversions
  - Validate time blocks against user-provided constraints (meetings, deadlines)
  - Support mid-day replanning

- **Conversation Context**
  - Maintain context within daily boundary
  - Remember key details for current day
  - Support natural follow-up questions
  - Clear context at midnight

## 4. System Architecture

### Core Components

#### Conversation Engine (LLM)
- Extract tasks and constraints from user messages
- Handle scheduled prompts (morning planning, evening reflection)
- Support explicit replanning requests
- Generate responses based on daily context
- Maintain current day's context

#### Calendar Manager
- Time block allocation and scheduling based on user-provided constraints
- Simple calendar link generation

#### Context Manager
- Store and retrieve today's conversation context
- Manage basic user preferences (timezone)
- Simple key-value store implementation
- Reset context daily at midnight
- Privacy-focused data handling
- No historical data retention (for MVP)

### Message Processing
- Handle incoming SMS via Twilio webhook
- Process scheduled prompts via cron jobs (7am planning, 8pm reflection)
- Direct message-response flow
- Simple error handling with user feedback

## 5. Data Model

### Core Entities

#### Task
```python
Task:
  id: UUID
  title: str
  description: Optional[str]
  due_date: Optional[DateTime]
  recurrence: Optional[RecurrencePattern]
  dependencies: List[TaskID]
  metadata: Dict[str, Any]
```

#### UserContext
```python
UserContext:
  preferences: Dict[str, Any]
  task_history: List[TaskHistory]
  interaction_patterns: Dict[str, Pattern]
```

## 6. LLM Integration

### Conversation Templates
- Morning planning
  - Task identification
  - Time constraint collection
  - Duration estimation
- Evening reflection
  - Task completion check
  - Next day preparation
- Replanning support
  - Constraint validation
  - New time block suggestions

### Template Management
- Simple text-based templates
- Include today's context:
  - Current task and schedule
  - User timezone
  - Today's conversation history

### Response Guidelines
- Clear, encouraging tone
- Specific time suggestions
- Simple yes/no questions when possible
- Explicit error messages

## 7. SMS Integration

### SMS Provider Integration (Twilio)
- Webhook endpoints for incoming messages
- Secure message delivery with retry mechanisms
- Phone number verification and management
- Rate limiting implementation
- Basic error handling and recovery

### Message Processing Flow
1. Receive incoming SMS via Twilio webhook
2. Validate message and phone number
3. Load today's context from Redis
4. Process message through LLM
5. Generate calendar links if needed
6. Update context and send response
7. Handle delivery status and errors

### Error Handling
- Graceful recovery from API failures
- Clear user communication during issues
- Automatic retry for failed messages
- Logging of errors without sensitive data

## 8. Testing Strategy

### Core Testing Areas
- SMS webhook handling
- LLM integration and responses
- Calendar link generation
- Context management
- Error recovery paths

### Integration Testing
- End-to-end message flow
- Twilio API integration
- Calendar API integration
- Redis operations
- Rate limiting behavior

### User Acceptance Testing
- Natural conversation flow
- Task scheduling accuracy
- Error message clarity
- Response time verification

## 9. Success Metrics

### Performance Metrics
- Response time < 1s
- 95% task parsing accuracy
- < 5% error rate
- 90% user satisfaction

### Business Metrics
- User retention
- Task completion rate
- Feature adoption
- User growth

## 10. Code Migration Plan

### Reusable Components
The following components from the existing codebase align with our MVP requirements and can be ported with minimal modification:

#### SMS Integration (message_handler.py)
Core message handling functionality to keep:

```python
from typing import Dict, Any
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

def process_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming message, keeping only essential fields"""
    return {
        'sender': data.get('From', ''),
        'timestamp': data.get('DateSent', ''),
        'content': data.get('Body', '').strip()
    }

def send_message(to: str, message: str):
    """Send SMS message via Twilio"""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        to=to,
        from_=TWILIO_PHONE_NUMBER
    )
```

Changes from original:
- Removed image handling
- Removed complex message processing
- Simplified data structure
- Added message content stripping
- Removed unnecessary logging

#### Calendar Integration (calendar_link_service.py)
Calendar link generation code to keep:

```python
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
```

Changes from original:
- Removed unnecessary logging
- Made location optional with default None
- Removed XML output parameter
- Simplified error handling
- Removed redundant comments

#### Twilio Integration (routes.py)
Webhook handling code to keep:

```python
from flask import Blueprint, request, current_app, Response
from twilio.twiml.messaging_response import MessagingResponse
from typing import Dict, Any

bp = Blueprint('sms', __name__, url_prefix='/sms')

def process_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming message, keeping only essential fields"""
    return {
        'sender': data.get('From', ''),
        'timestamp': data.get('DateSent', ''),
        'content': data.get('Body', '').strip()
    }

@bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming SMS messages"""
    try:
        # Process incoming message
        message = process_message(request.form)
        
        # Handle media if present
        if request.values.get('NumMedia', '0') != '0':
            media_url = request.values.get('MediaUrl0', '')
            if media_url:
                response_text = "Image received but processing is not implemented yet."
            else:
                response_text = "Image processing failed: No image received"
        else:
            response_text = "Message received! We'll process it shortly."
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        
        return Response(str(resp), mimetype="application/xml")
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        error_resp = MessagingResponse()
        error_resp.message("Sorry, we encountered an error processing your message.")
        return Response(str(error_resp), mimetype="application/xml"), 200
```

Changes from original:
- Moved to Blueprint structure with `/sms` prefix
- Enhanced error handling with proper TwiML responses
- Added media handling support (placeholder)
- Improved response formatting with correct MIME type
- Added structured message processing
- Simplified logging

Development Setup:
```bash
# Install ngrok
pip install pyngrok>=7.2.0

# Start Flask app
flask run

# In separate terminal, start ngrok
ngrok http 5000

# Update Twilio webhook URL with ngrok URL + /sms/webhook
```

### Components to Build New
To maintain the MVP's focus on simplicity, we'll build new implementations for:

- **Context Manager**
  - Daily task storage
  - Timezone preferences
  - Midnight reset logic

- **LLM Integration**
  - Morning planning templates
  - Evening reflection templates
  - Replanning templates

- **Error Handling**
  - Basic logging
  - User-friendly error messages
  - Privacy-focused error reporting

This approach ensures we maintain the MVP's core principle of "Do One Thing Well" while leveraging proven code where appropriate.

## 11. Components to Rebuild

### Core Components Analysis

1. **Daily Task Storage**
   - **Purpose**: Store only today's task and timezone
   - **Integration Points**: 
     - Receives task from morning planning
     - Provides task info for calendar link
   - **Alternative Approach**: 
     - Simple Redis key-value store
     - Key: user_phone_YYYYMMDD
     - Value: JSON with task and timezone only
     - Auto-expire at midnight

2. **LLM Integration**
   - **Purpose**: Extract task and time constraints
   - **Integration Points**:
     - Receives raw message
     - Outputs structured task data
   - **Alternative Approach**:
     - Single function call with clear schema
     - No conversation tracking needed
     - Just extract: task, duration, constraints

3. **Main Application Flow**
   - **Purpose**: Handle webhooks and coordinate responses
   - **Integration Points**:
     - Twilio webhook entry
     - LLM task extraction
     - Calendar link generation
   - **Alternative Approach**:
     - Single Flask app
     - Direct function calls
     - No state management needed

### Simplified Architecture
```
Morning/Evening Webhook → LLM Extract → Store Task → Calendar Link → Response
Ad-hoc Webhook → LLM Extract → Calendar Link → Response
```

Key Differences:
1. No conversation state
2. No complex workflows
3. Just task and timezone storage
4. Direct function calls
5. Focus on immediate scheduling

This suggests:
1. Skip message_handler.py - too complex
2. Keep calendar_link_service.py
3. Build everything else minimal

The key is keeping only what's needed for immediate task scheduling, nothing more.

## 12. Project Structure

anchor/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── routes.py            # SMS webhook endpoints
│   ├── calendar_service.py  # Calendar link generation (ported)
│   ├── llm.py              # LLM function calling
│   └── storage.py          # Redis task storage
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration (env vars)
├── tests/
│   ├── __init__.py
│   ├── test_routes.py      # SMS webhook tests
│   ├── test_calendar.py    # Calendar link tests
│   └── test_llm.py        # LLM integration tests
├── .env.example            # Environment variables template
├── .gitignore
├── README.md              # Project documentation
├── requirements.txt       # Dependencies including pyngrok
└── run.py                # Application entry point

Key files needed:

1. **requirements.txt**:
```
Flask==3.0.0
redis==5.0.1
python-dotenv==1.0.0
twilio==8.10.0
pyngrok>=7.2.0
python-dateutil==2.8.2
```

2. **.env.example**:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=your_number_here
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_key_here
```

## 13. Ported Components

### Ngrok and Twilio Integration
We've ported and simplified the ngrok/Twilio integration from the original project, maintaining its core functionality while improving error handling and response processing:

1. **Dependencies Added**:
   ```
   pyngrok>=7.2.0  # For local development tunneling
   ```

2. **Environment Variables**:
   ```
   TWILIO_ACCOUNT_SID=your-account-sid-from-twilio
   TWILIO_AUTH_TOKEN=your-auth-token-from-twilio
   TWILIO_PHONE_NUMBER=your-twilio-phone-number
   ```

3. **Webhook Handler**:
   - Endpoint: `/sms/webhook`
   - Enhanced error handling with proper TwiML responses
   - Media handling support (placeholder for future implementation)
   - Structured message processing

4. **Key Improvements**:
   - Moved to Blueprint structure (`/sms` prefix)
   - Added proper error logging
   - Improved response handling
   - Maintained XML MIME type for all responses
   - Added media handling scaffolding

5. **Development Setup**:
   - Run Flask app on port 5000
   - Use separate ngrok process for tunneling
   - Update Twilio webhook URL with ngrok URL

This integration maintains the reliable webhook handling of the original while adding structure and error handling improvements that align with the MVP's focus on simplicity and reliability.
