from flask import Blueprint, request, current_app, Response
from typing import Dict, Any
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app.calendar_service import CalendarLinkService, EventDetails

# Changed url_prefix to '' to match Twilio's webhook configuration
bp = Blueprint('sms', __name__, url_prefix='') #none for now, may add /sms as prefix in the future

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
        
    if "menu" in content:
        return ("Here's what I can help you with:\n"
                "📝 Tell me your most important task for today\n"
                "🕒 Ask me to reschedule a task\n"
                "✓ Check your task status\n\n"
                "Reply with 'menu' anytime to see this list again!")
                
    # Default response for first-time or unclear messages
    return ("Welcome! I'm your task planning assistant. 👋\n"
            "Tell me your most important task for today, or reply with 'menu' to see what else I can do!")

@bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming SMS messages"""
    try:
        # Log raw request data
        current_app.logger.info(f"Received webhook request with data: {request.form}")
        
        # Process incoming message
        message = process_message(request.form)
        current_app.logger.info(f"Received message: {message}")
        
        # Handle media if present
        if request.values.get('NumMedia', '0') != '0':
            media_url = request.values.get('MediaUrl0', '')
            if media_url:
                response_text = "I've received your image, but I can only process text messages for now."
                current_app.logger.info("Received image message")
            else:
                response_text = "I received a media message but couldn't process it. Please send text only."
                current_app.logger.info("Received media without URL")
        else:
            # Process the text message
            response_text = handle_text_message(message)
            current_app.logger.info(f"Sending response: {response_text}")
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        return Response(str(resp), mimetype='text/xml')
        
    except Exception as e:
        current_app.logger.error(f"Error processing message: {str(e)}")
        resp = MessagingResponse()
        resp.message("I encountered an error processing your message. Please try again.")
        return Response(str(resp), mimetype='text/xml')