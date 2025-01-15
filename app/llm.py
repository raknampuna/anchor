"""
LLM Service for Anchor task planning.
Handles task extraction, scheduling suggestions, and response generation.
Focuses on immediate task scheduling without maintaining complex state.
"""

from typing import Dict, Any, Optional, Tuple
import os
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

from app.schema import LLMResponse, MessageType
from app.storage import RedisStorage
from config.settings import REDIS_URL

# Load environment variables
load_dotenv()

class LLMService:
    def __init__(self):
        """Initialize Gemini model and Redis storage"""
        try:
            # Initialize Gemini
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "GOOGLE_API_KEY environment variable not set. "
                    "Please set it to your Google API key."
                )
            
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel('gemini-pro')
            
            # Initialize Redis storage
            self._storage = RedisStorage(REDIS_URL)
            
        except Exception as e:
            print(f"Error initializing LLM service: {str(e)}")
            print("\nPlease ensure you have:")
            print("1. Set GOOGLE_API_KEY environment variable")
            print("2. Redis server running")
            raise

    def process_message(
        self,
        user_id: str,
        message: str,
        message_type: Optional[str] = None
    ) -> LLMResponse:
        """Process message and maintain context in Redis"""
        try:
            # Get existing context or create new
            context = self._storage.get_context(user_id) or {
                "message_type": message_type or MessageType.AD_HOC,
                "current_task": None,
                "timing": None,
                "last_interaction": datetime.now().isoformat()
            }
            
            chat = self._model.start_chat()
            current_time = datetime.now().strftime("%I:%M %p")
            
            # Build the conversation prompt
            conversation_prompt = f"""You are Anchor, an AI assistant focused on helping users plan and complete their most important task each day.

Current time: {current_time}
User message: "{message}"

Current context:
Task: {context.get('current_task', 'Not set yet')}
Message Type: {context.get('message_type', MessageType.AD_HOC)}
Timing: {json.dumps(context.get('timing', {}), indent=2) if context.get('timing') else 'Not set'}

Your goal is to help users:
1. Identify their most important task for today
2. Understand when they need to do it
3. Find the best time to schedule it
4. Keep them focused and motivated

Based on the current message type ({context.get('message_type', MessageType.AD_HOC)}):
- MORNING_PLANNING: Help identify and schedule the day's most important task
- REPLANNING: Help adjust the schedule based on new constraints
- EVENING_REFLECTION: Capture task completion and learnings
- AD_HOC: Handle general inquiries while keeping focus on the main task

Extract any timing information from the message:
- Task duration (e.g., "2 hours", "30 minutes")
- Deadlines (e.g., "by 2 PM", "before lunch")
- Time constraints (e.g., "meeting at 11 AM", "busy until 3")
- Preferred times (e.g., "around 3 PM", "in the morning")

Respond in two parts:
1. A natural, conversational response (format: "RESPONSE: your response here")
2. Structured information (format: "INFO: {{
    "task": string or null,
    "message_type": string,
    "timing": {{
        "duration_minutes": number or null,
        "deadline": "HH:MM" or null,
        "preferred_time": "HH:MM" or null,
        "constraints": [
            {{
                "start_time": "HH:MM",
                "end_time": "HH:MM",
                "description": string,
                "is_focus_block": boolean
            }}
        ]
    }} or null
}}")

Example:
RESPONSE: Hi! I see you want to schedule a call with your mom at 3 PM. Would you like me to block out some time for that?
INFO: {{
    "task": "Call Mom",
    "message_type": "ad_hoc",
    "timing": {{
        "preferred_time": "15:00",
        "duration_minutes": 30,
        "deadline": null,
        "constraints": []
    }}
}}"""

            print("\n=== Sending Prompt to LLM ===")
            print("Prompt:", conversation_prompt)
            
            # Get response from LLM
            llm_raw_response = chat.send_message(conversation_prompt).text.strip()
            print("\n=== Raw LLM Response ===")
            print(llm_raw_response)
            
            llm_response = LLMResponse.from_llm_output(llm_raw_response)
            
            # Update context with new information
            context.update({
                "current_task": llm_response.task or context.get("current_task"),
                "message_type": llm_response.message_type or context.get("message_type"),
                "timing": llm_response.timing.model_dump() if llm_response.timing else context.get("timing"),
                "last_interaction": datetime.now().isoformat()
            })
            
            # Save updated context
            self._storage.save_context(user_id, context)
            
            return llm_response  # Return full LLMResponse object
            
        except Exception as e:
            print(f"\n=== Error in process_message ===")
            print(f"Error: {str(e)}")
            # Return a valid LLMResponse object for error case
            return LLMResponse(
                response="I'm having trouble processing your message. Let's focus on your task - what would you like to accomplish today?",
                task=None,
                message_type=MessageType.AD_HOC,
                timing=None
            )