#!/usr/bin/env python3
"""
Interactive CLI for testing the LLM Service.
Run this script to simulate SMS conversations with the LLM.
"""

import sys
import os
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core components
from app import LLMService, MessageType

# Test user ID for Redis storage
TEST_USER_ID = "test_user"

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

def print_context(llm: LLMService):
    """Pretty print the current context from Redis"""
    context = llm._storage.get_context(TEST_USER_ID)
    if not context:
        print("\nNo context found")
        return
        
    print("\nCurrent Context:")
    print(f"Message Type: {context.get('message_type', 'Not set')}")
    print(f"Current Task: {context.get('current_task', 'Not set')}")
    print(f"Last Interaction: {context.get('last_interaction', 'Never')}")

def change_message_type(llm: LLMService, type_str: str):
    """Change the message type in context"""
    type_map = {
        "morning": MessageType.MORNING_PLANNING,
        "replan": MessageType.REPLANNING,
        "evening": MessageType.EVENING_REFLECTION,
        "adhoc": MessageType.AD_HOC
    }
    
    if type_str not in type_map:
        print(f"\nUnknown type: {type_str}")
        print("Available types: morning, replan, evening, adhoc")
        return
        
    # Get current context or create new
    context = llm._storage.get_context(TEST_USER_ID) or {}
    context["message_type"] = type_map[type_str]
    context["last_interaction"] = datetime.now().isoformat()
    
    # Save updated context
    llm._storage.save_context(TEST_USER_ID, context)
    print(f"\nChanged message type to: {type_map[type_str]}")

def main():
    """Run the interactive CLI"""
    llm = LLMService()
    
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
                elif cmd == "clear":
                    llm._storage.save_context(TEST_USER_ID, {})
                    print("\nContext cleared!")
                elif cmd == "context":
                    print_context(llm)
                elif cmd == "time":
                    print(f"\nCurrent time: {datetime.now().strftime('%I:%M %p')}")
                elif cmd.startswith("type"):
                    # Handle /type morning, /type evening, etc.
                    parts = cmd.split(maxsplit=1)
                    if len(parts) > 1:
                        change_message_type(llm, parts[1])
                elif cmd == "quit":
                    print("\nGoodbye!")
                    break
                else:
                    print(f"\nUnknown command: {cmd}")
                    print_help()
                continue
            
            # Print current context
            print("\n=== Current Context ===")
            print_context(llm)
            
            # Process message through LLM
            print("\n=== Sending Message to LLM ===")
            print(f"Message: {message}")
            
            try:
                response = llm.process_message(TEST_USER_ID, message)
                print("\n=== LLM Response ===")
                print(f"A: {response}")
            except Exception as e:
                print(f"\n=== Error Processing Message ===")
                print(f"Error: {str(e)}")
                print("A: I'm having trouble processing your message. Let's focus on your task - what would you like to accomplish today?")
            
            # Show updated context
            print("\n=== Updated Context ===")
            print_context(llm)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue

if __name__ == "__main__":
    main()