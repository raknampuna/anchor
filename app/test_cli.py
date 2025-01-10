#!/usr/bin/env python3
"""
Interactive CLI for testing the LLM Service.
Run this script to simulate SMS conversations with the LLM.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm import LLMService
from app.schema import UserContext, MessageType
from datetime import datetime

def print_help():
    """Print available commands"""
    print("\nAvailable commands:")
    print("  /help     - Show this help message")
    print("  /clear    - Clear current context")
    print("  /context  - Show current context")
    print("  /time     - Show current time")
    print("  /type     - Change message type (morning/replan/evening)")
    print("  /quit     - Exit the program")
    print("\nJust type your message to chat with the LLM!")

def print_context(context: UserContext):
    """Pretty print the current context"""
    print("\nCurrent Context:")
    print(f"Message Type: {context.message_type}")
    print(f"Last Interaction: {context.last_interaction}")
    
    if context.current_task:
        print("\nCurrent Task:")
        print(f"  Description: {context.current_task.task}")
        print(f"  Duration: {context.current_task.duration_minutes} minutes")
        print(f"  Constraints: {context.current_task.constraints}")
        
        if context.current_task.time_block:
            print(f"  Scheduled: {context.current_task.time_block.start_time} - {context.current_task.time_block.end_time}")
        
        if context.current_task.completion:
            print("\nTask Completion:")
            print(f"  Completed: {context.current_task.completion.completed}")
            print(f"  Follow-up: {context.current_task.completion.follow_up_task}")
            print(f"  Learnings: {context.current_task.completion.learnings}")

def change_message_type(context: UserContext, type_str: str) -> UserContext:
    """Change the message type"""
    type_map = {
        "morning": MessageType.MORNING_PLANNING,
        "replan": MessageType.REPLANNING,
        "evening": MessageType.EVENING_REFLECTION,
        "adhoc": MessageType.AD_HOC
    }
    
    if type_str in type_map:
        context.message_type = type_map[type_str]
        print(f"\nChanged message type to: {context.message_type}")
    else:
        print(f"\nUnknown type: {type_str}")
        print("Available types: morning, replan, evening, adhoc")
    
    return context

def main():
    """Run the interactive CLI"""
    llm = LLMService()
    context = UserContext()
    
    print("\nAnchor Task Planning CLI")
    print("=" * 50)
    print_help()
    print("\nType your message (or /help for commands):")
    
    while True:
        try:
            # Get user input
            message = input("\nYou: ").strip()
            
            # Handle commands
            if message.startswith("/"):
                cmd = message[1:].lower()
                if cmd == "help":
                    print_help()
                    continue
                elif cmd == "clear":
                    context = UserContext()
                    print("\nContext cleared!")
                    continue
                elif cmd == "context":
                    print_context(context)
                    continue
                elif cmd == "time":
                    print(f"\nCurrent time: {datetime.now().strftime('%I:%M %p')}")
                    continue
                elif cmd.startswith("type"):
                    # Handle /type morning, /type evening, etc.
                    parts = cmd.split(maxsplit=1)
                    if len(parts) > 1:
                        context = change_message_type(context, parts[1])
                    else:
                        print("\nUsage: /type [morning|replan|evening|adhoc]")
                    continue
                elif cmd == "quit":
                    print("\nGoodbye!")
                    return
                else:
                    print(f"\nUnknown command: {message}")
                    print("Type /help for available commands")
                    continue
            
            # Process message through LLM
            response, context = llm.process_message(message, context)
            print(f"\nAssistant: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            return
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Type /help for available commands")

if __name__ == "__main__":
    main()