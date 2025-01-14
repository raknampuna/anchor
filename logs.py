#!/usr/bin/env python3
# logs.py

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
import re
import time

class LogAnalyzer:
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = Path(base_dir)
        
    def get_phone_logs(self, phone_number: str) -> Path:
        return self.base_dir / "phone_numbers" / phone_number
        
    def parse_time(self, time_str: str) -> datetime:
        """Parse time strings like '2h ago', '24h', '7d'"""
        if time_str.endswith(" ago") or time_str.endswith("ago"):
            time_str = time_str.replace(" ago", "").replace("ago", "")
        
        if time_str.endswith("h"):
            hours = int(time_str[:-1])
            return datetime.utcnow() - timedelta(hours=hours)
        elif time_str.endswith("d"):
            days = int(time_str[:-1])
            return datetime.utcnow() - timedelta(days=days)
        else:
            return datetime.fromisoformat(time_str)
            
    def filter_log(self, entry: dict, args: argparse.Namespace) -> bool:
        """Apply filters to log entry"""
        if args.level and entry["level"] != args.level:
            return False
            
        if args.event_type and entry["event_type"] != args.event_type:
            return False
            
        if args.since:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time < self.parse_time(args.since):
                return False
                
        if args.component and entry["data"]["component"] != args.component:
            return False
            
        if args.status and entry["data"]["status"] != args.status:
            return False
            
        if args.error_type and entry["data"].get("error_type") != args.error_type:
            return False
            
        if args.duration:
            op, val = re.match(r"([<>])(\d+)", args.duration).groups()
            dur = entry["data"].get("duration_ms", 0)
            if op == ">" and dur <= int(val):
                return False
            if op == "<" and dur >= int(val):
                return False
                
        if args.contains and args.contains.lower() not in entry["data"]["message"].lower():
            return False
            
        if args.pattern and not re.search(args.pattern, entry["data"]["message"]):
            return False
            
        return True
        
    def view_logs(self, phone_number: str, args: argparse.Namespace):
        """View logs for a specific phone number"""
        log_file = self.get_phone_logs(phone_number) / "consolidated.log"
        
        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)
                if self.filter_log(entry, args):
                    self.print_entry(entry)
                    
    def follow_logs(self, phone_number: str, args: argparse.Namespace):
        """Follow logs in real-time"""
        log_file = self.get_phone_logs(phone_number) / "consolidated.log"
        
        with open(log_file) as f:
            # First, read existing content
            for line in f:
                entry = json.loads(line)
                if self.filter_log(entry, args):
                    self.print_entry(entry)
            
            # Then follow new content
            while True:
                line = f.readline()
                if line:
                    entry = json.loads(line)
                    if self.filter_log(entry, args):
                        self.print_entry(entry)
                else:
                    time.sleep(0.1)
                    
    def print_entry(self, entry: dict):
        """Pretty print a log entry"""
        # Add colors based on level
        colors = {
            "ERROR": "\033[91m",  # Red
            "WARNING": "\033[93m",  # Yellow
            "INFO": "\033[92m",  # Green
            "END": "\033[0m"
        }
        
        level_color = colors.get(entry["level"], "")
        print(f"{level_color}[{entry['timestamp']}] {entry['level']}: {entry['data']['message']}{colors['END']}")

def main():
    parser = argparse.ArgumentParser(description="Anchor Log Analysis Tool")
    parser.add_argument("command", choices=["view", "follow", "search", "summary"])
    parser.add_argument("phone_number", help="Phone number to analyze")
    
    # Filter options
    parser.add_argument("--level", choices=["INFO", "WARNING", "ERROR"])
    parser.add_argument("--since", help="Show logs since (e.g., '2h ago', '2025-01-13')")
    parser.add_argument("--event-type", help="Filter by event type")
    parser.add_argument("--component", help="Filter by component")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--error-type", help="Filter by error type")
    parser.add_argument("--duration", help="Filter by duration (e.g., '>5000')")
    parser.add_argument("--contains", help="Filter by message content")
    parser.add_argument("--pattern", help="Filter by regex pattern")
    
    args = parser.parse_args()
    analyzer = LogAnalyzer()
    
    if args.command == "view":
        analyzer.view_logs(args.phone_number, args)
    elif args.command == "follow":
        analyzer.follow_logs(args.phone_number, args)
    # TODO: Implement search and summary commands
    
if __name__ == "__main__":
    main()