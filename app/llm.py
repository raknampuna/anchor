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

from app.schema import LLMResponse, UserContext, MessageType, TaskInfo, TimeBlock

# Load environment variables
load_dotenv()

class LLMService:
    def __init__(self):
        """Initialize Gemini model for task processing"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "GOOGLE_API_KEY environment variable not set. "
                    "Please set it to your Google API key."
                )
            
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel('gemini-pro')
            
        except Exception as e:
            print(f"Error initializing LLM service: {str(e)}")
            print("\nPlease ensure you have:")
            print("1. Set GOOGLE_API_KEY environment variable")
            print("2. Obtained an API key from https://makersuite.google.com/")
            raise

    def process_message(
        self,
        message: str,
        context: Optional[UserContext] = None
    ) -> Tuple[str, UserContext]:
        """Process message based on context and content."""
        if context is None:
            context = UserContext()
            
        chat = self._model.start_chat()
        current_time = datetime.now().strftime("%I:%M %p")
        
        try:
            # Build the conversation prompt
            conversation_prompt = f"""You are Anchor, an AI assistant focused on helping users plan and complete their most important task each day.

Current time: {current_time}
User message: "{message}"

Current context:
Task: {context.current_task.task if context.current_task else 'Not set yet'}
Duration: {context.current_task.duration_minutes if context.current_task else 'Unknown'} minutes
Constraints: {context.current_task.constraints if context.current_task else []}
Time Block: {context.current_task.time_block.dict() if context.current_task and context.current_task.time_block else 'Not scheduled'}
Message Type: {context.message_type}

Your goal is to help users:
1. Identify their most important task for today
2. Understand when they need to do it
3. Find the best time to schedule it
4. Keep them focused and motivated

Based on the current message type ({context.message_type}):
- MORNING_PLANNING: Help identify and schedule the day's most important task
- REPLANNING: Help adjust the schedule based on new constraints
- EVENING_REFLECTION: Capture task completion and learnings
- AD_HOC: Handle general inquiries while keeping focus on the main task

Respond in two parts:
1. A natural, conversational response (format: "RESPONSE: your response here")
2. Structured information (format: "INFO: {{
    "task": string or null,
    "duration_minutes": number or null,
    "constraints": [string],
    "time_block": {{"start_time": "HH:MM", "end_time": "HH:MM"}} or null,
    "completion": {{"completed": boolean, "follow_up_task": string or null, "learnings": string or null}} or null
}}")

Remember:
- Keep responses natural and friendly
- Extract any task information from the message
- Suggest specific time blocks when enough information is available
- For evening reflection, capture completion status and learnings
- Return valid JSON in the INFO section

Example Evening Reflection:
RESPONSE: Great job today! I see you completed the presentation. Any particular challenges you'd like to tackle tomorrow?
INFO: {{"task": "Q1 presentation", "completion": {{"completed": true, "follow_up_task": "prepare speaking notes", "learnings": "need more time for design work"}}, "time_block": null, "duration_minutes": null, "constraints": []}}"""

            # Get response from LLM
            llm_response = LLMResponse.from_llm_output(
                chat.send_message(conversation_prompt).text.strip()
            )
            
            # Update context
            updated_context = llm_response.update_context(context)
            
            # Determine next message type
            if "tomorrow" in message.lower() or "next" in message.lower():
                updated_context.message_type = MessageType.MORNING_PLANNING
            elif "replan" in message.lower() or "change" in message.lower():
                updated_context.message_type = MessageType.REPLANNING
            elif self._is_evening_time():
                updated_context.message_type = MessageType.EVENING_REFLECTION
            
            return llm_response.response, updated_context
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            # Provide context-aware fallback responses
            if context.message_type == MessageType.MORNING_PLANNING:
                return "Let's focus on your most important task for today. What would you like to accomplish?", context
            elif context.message_type == MessageType.EVENING_REFLECTION:
                return "How did today's task go?", context
            else:
                return "I'm here to help you plan and complete your important task. What's on your mind?", context

    def _is_evening_time(self) -> bool:
        """Check if it's evening reflection time (7 PM - 9 PM)"""
        hour = datetime.now().hour
        return 19 <= hour <= 21