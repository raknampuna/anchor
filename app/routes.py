from flask import Blueprint, request, current_app, Response
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app.calendar_service import CalendarLinkService, EventDetails
from app.llm import LLMService
from app.schema import LLMResponse, MessageType, TaskTiming
from datetime import datetime, timedelta

# Create a Flask Blueprint for SMS functionality
# No url_prefix is specified because:
# 1. Twilio needs to hit the webhook endpoint at exactly /webhook
# 2. Adding a prefix would require updating the Twilio console URL
# 3. We might add /sms prefix in the future if we need to organize multiple feature sets
bp = Blueprint('sms', __name__)  # Remove url_prefix completely, may add /sms as prefix in the future

# Initialize services
llm_service = LLMService()
calendar_service = CalendarLinkService()

def process_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming message, keeping only essential fields"""
    return {
        'sender': data.get('From', ''),
        'timestamp': data.get('DateSent', ''),
        'content': data.get('Body', '').strip()
    }

def send_message(to: str, message: str):
    """Send SMS message via Twilio"""
    client = Client(
        current_app.config['TWILIO_ACCOUNT_SID'],
        current_app.config['TWILIO_AUTH_TOKEN']
    )
    client.messages.create(
        body=message,
        to=to,
        from_=current_app.config['TWILIO_PHONE_NUMBER']
    )

def create_calendar_event(task: str, timing: TaskTiming) -> Optional[str]:
    """Create calendar event if timing information is complete"""
    if not timing or not timing.preferred_time:
        return None
        
    try:
        # Convert preferred time to datetime
        schedule_time = datetime.strptime(timing.preferred_time, "%H:%M").time()
        event_date = datetime.now().date()
        start_time = datetime.combine(event_date, schedule_time)
        
        # Default to 30 min if duration not specified
        duration = timing.duration_minutes or 30
        end_time = start_time + timedelta(minutes=duration)
        
        event = EventDetails(
            title=task,
            description="Task scheduled via Anchor",
            start_time=start_time,
            end_time=end_time
        )
        
        return calendar_service.create_calendar_link(event)
    except Exception as e:
        current_app.logger.error(f"Error creating calendar event: {str(e)}")
        return None

@bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming SMS messages"""
    try:
        # Log raw request data
        current_app.logger.info(f"Received webhook request with data: {request.form}")
        
        # Process incoming message
        message = process_message(request.form)
        current_app.logger.info(f"Received message: {message}")
        
        # Process with LLM and get structured response
        llm_response = llm_service.process_message(
            user_id=message['sender'],
            message=message['content']
        )
        
        response_text = llm_response.response
        
        # If we have a task and timing, create calendar event
        if llm_response.task and llm_response.timing:
            calendar_link = create_calendar_event(
                llm_response.task,
                llm_response.timing
            )
            if calendar_link:
                response_text += f"\n\nAdd to calendar: {calendar_link}"
        
        current_app.logger.info(f"Sending response: {response_text}")
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        return Response(str(resp), mimetype='text/xml')
        
    except Exception as e:
        current_app.logger.error(f"Error processing message: {str(e)}")
        # Return friendly error message
        resp = MessagingResponse()
        resp.message("I'm having trouble processing your message. Please try again in a moment.")
        return Response(str(resp), mimetype='text/xml')