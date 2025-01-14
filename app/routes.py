from flask import Blueprint, request, current_app, Response
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app.calendar_service import CalendarLinkService, EventDetails
from app.llm import LLMService
from app.schema import LLMResponse, MessageType, TaskTiming
from datetime import datetime, timedelta
from app.logging import log_interaction, log_llm, log_error, log_system
import time

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
    try:
        client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )
        client.messages.create(
            body=message,
            to=to,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )
        log_interaction(to, f"Sent message: {message}", status="success")
    except Exception as e:
        log_error(to, f"Failed to send message: {str(e)}", error_type="twilio_error")
        raise

def create_calendar_event(task: str, timing: TaskTiming, phone_number: str) -> Optional[str]:
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
        
        link = calendar_service.create_calendar_link(event)
        if link:
            log_system(phone_number, f"Created calendar event: {task}", 
                      extra_data={"event": event.dict(), "link": link})
        return link
    except Exception as e:
        log_error(phone_number, f"Error creating calendar event: {str(e)}", 
                 error_type="calendar_error",
                 extra_data={"task": task, "timing": timing.dict()})
        return None

@bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming SMS messages"""
    start_time = time.time()
    session_id = None
    
    try:
        # Process incoming message
        message = process_message(request.form)
        phone_number = message['sender']
        
        # Log incoming message
        log_interaction(
            phone_number=phone_number,
            message=f"Received: {message['content']}",
            extra_data={"raw_data": dict(request.form)}
        )
        
        # Process with LLM and get structured response
        llm_start = time.time()
        llm_response = llm_service.process_message(
            user_id=phone_number,
            message=message['content']
        )
        llm_duration = int((time.time() - llm_start) * 1000)
        
        # Log LLM response
        log_llm(
            phone_number=phone_number,
            message=f"LLM Response: {llm_response.response}",
            duration_ms=llm_duration,
            extra_data={
                "task": llm_response.task,
                "message_type": llm_response.message_type,
                "timing": llm_response.timing.dict() if llm_response.timing else None
            }
        )
        
        response_text = llm_response.response
        
        # If we have a task and timing, create calendar event
        if llm_response.task and llm_response.timing:
            calendar_link = create_calendar_event(
                llm_response.task,
                llm_response.timing,
                phone_number
            )
            if calendar_link:
                response_text += f"\n\nAdd to calendar: {calendar_link}"
        
        # Create and send TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        
        # Log total processing time
        total_duration = int((time.time() - start_time) * 1000)
        log_system(
            phone_number=phone_number,
            message="Request completed successfully",
            duration_ms=total_duration,
            status="success"
        )
        
        return Response(str(resp), mimetype='text/xml')
        
    except Exception as e:
        # Log error with full context
        log_error(
            phone_number=message['sender'] if 'message' in locals() else "unknown",
            message=f"Error processing message: {str(e)}",
            error_type=type(e).__name__,
            duration_ms=int((time.time() - start_time) * 1000),
            status="failed",
            extra_data={"traceback": str(e)}
        )
        
        # Return friendly error message
        resp = MessagingResponse()
        resp.message("I'm having trouble processing your message. Please try again in a moment.")
        return Response(str(resp), mimetype='text/xml')