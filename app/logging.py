# app/logging.py

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

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
        
    def create_log_entry(
        self,
        level: str,
        event_type: str,
        phone_number: str,
        message: str,
        component: str,
        duration_ms: Optional[int] = None,
        related_events: Optional[List[str]] = None,
        status: str = "success",
        error_type: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Create a structured log entry"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "event_type": event_type,
            "phone_number": phone_number,
            "data": {
                "message": message,
                "component": component,
                "duration_ms": duration_ms,
                "related_events": related_events or [],
                "status": status,
                "error_type": error_type,
                **(extra_data or {})
            },
            "metadata": {
                "session_id": str(uuid.uuid4()),
                "version": "1.0",
                "trace_id": str(uuid.uuid4())
            }
        }
        return entry

    def write_log(self, entry: dict):
        """Write a log entry to both consolidated and type-specific logs"""
        phone_dir = self.get_phone_dir(entry["phone_number"])
        
        # Write to consolidated log
        with open(phone_dir / "consolidated.log", "a") as f:
            json.dump(entry, f)
            f.write("\n")
            
        # Write to type-specific log
        type_file = phone_dir / "by_type" / f"{entry['event_type']}.log"
        with open(type_file, "a") as f:
            json.dump(entry, f)
            f.write("\n")

    def log(
        self,
        level: str,
        event_type: str,
        phone_number: str,
        message: str,
        component: str,
        **kwargs
    ):
        """Main logging interface"""
        entry = self.create_log_entry(
            level=level,
            event_type=event_type,
            phone_number=phone_number,
            message=message,
            component=component,
            **kwargs
        )
        self.write_log(entry)

# Create global logger instance
logger = AnchorLogger()

# Convenience methods
def log_interaction(phone_number: str, message: str, **kwargs):
    logger.log("INFO", "user_interaction", phone_number, message, "sms", **kwargs)

def log_llm(phone_number: str, message: str, **kwargs):
    logger.log("INFO", "llm_response", phone_number, message, "llm", **kwargs)

def log_error(phone_number: str, message: str, error_type: str, **kwargs):
    logger.log("ERROR", "error", phone_number, message, "system", 
               error_type=error_type, status="failed", **kwargs)

def log_system(phone_number: str, message: str, **kwargs):
    logger.log("INFO", "system", phone_number, message, "system", **kwargs)