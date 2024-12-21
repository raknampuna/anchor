from flask import Blueprint, request, current_app, Response
from typing import Dict, Any
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app.calendar_service import CalendarLinkService, EventDetails

bp = Blueprint('sms', __name__, url_prefix='/sms')

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

def handle_text_message(message: Dict[str, Any]) -> str:
    """Process text messages and generate appropriate responses"""
    content = message['content'].lower()
    
    # Basic response logic - we'll expand this later with LLM
    if not content:
        return "I didn't receive any message content. Please try again."
        
    if "help" in content:
        return ("I'm your personal task planner. You can:\n"
                "- Tell me your most important task for today\n"
                "- Ask me to reschedule a task\n"
                "- Check your task status")
                
    # Default response for now
    return ("I've received your message! While I'm still learning, "
            "I'll be able to help you plan and schedule your tasks soon.")

@bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming SMS messages"""
    try:
        # Process incoming message
        message = process_message(request.form)
        current_app.logger.info(f"Received message: {message}")
        
        # Handle media if present
        if request.values.get('NumMedia', '0') != '0':
            media_url = request.values.get('MediaUrl0', '')
            if media_url:
                response_text = "I've received your image, but I can only process text messages for now."
            else:
                response_text = "I received a media message but couldn't process it. Please send text only."
        else:
            # Process the text message
            response_text = handle_text_message(message)
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        return Response(str(resp), mimetype='text/xml')
        
    except Exception as e:
        current_app.logger.error(f"Error processing message: {str(e)}")
        resp = MessagingResponse()
        resp.message("I encountered an error processing your message. Please try again.")
        return Response(str(resp), mimetype='text/xml')