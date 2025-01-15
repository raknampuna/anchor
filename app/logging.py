# app/logging.py

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class AnchorLogger:
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = Path(base_dir)
        self.setup_directory_structure()
        
    def setup_directory_structure(self):
        """Create the base logging directory structure"""
        self.base_dir.mkdir(exist_ok=True)
        (self.base_dir / "phone_numbers").mkdir(exist_ok=True)
        
    def get_phone_dir(self, phone_number: str) -> Path:
        """Get directory for a specific phone number, creating if needed"""
        phone_dir = self.base_dir / "phone_numbers" / phone_number
        phone_dir.mkdir(exist_ok=True)
        (phone_dir / "by_type").mkdir(exist_ok=True)
        return phone_dir

    def write_log(self, phone_number: str, level: str, message: str, event_type: str):
        """Write a log entry to both consolidated and type-specific logs"""
        timestamp = datetime.now().isoformat()
        log_line = f"{timestamp} - {level} - {message}\n"
        
        phone_dir = self.get_phone_dir(phone_number)
        
        # Write to consolidated log
        with open(phone_dir / "consolidated.log", "a") as f:
            f.write(log_line)
            
        # Write to type-specific log
        type_file = phone_dir / "by_type" / f"{event_type}.log"
        with open(type_file, "a") as f:
            f.write(log_line)

# Create global logger instance
logger = AnchorLogger()

def log_interaction(phone_number: str, message: str, **kwargs):
    """Log user interaction"""
    logger.write_log(phone_number, "INFO", message, "interaction")

def log_llm(phone_number: str, message: str, **kwargs):
    """Log LLM response"""
    logger.write_log(phone_number, "INFO", message, "llm")

def log_error(phone_number: str, message: str, error_type: str, **kwargs):
    """Log error"""
    logger.write_log(phone_number, "ERROR", message, "error")

def log_system(phone_number: str, message: str, **kwargs):
    """Log system message"""
    logger.write_log(phone_number, "INFO", message, "system")