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
            
    def parse_log_line(self, line: str) -> dict:
        """Parse a log line into components"""
        match = re.match(r'\[(.*?)\] (\w+): (.*)', line.strip())
        if not match:
            return None
        timestamp, level, message = match.groups()
        return {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
            
    def filter_log(self, entry: dict, args: argparse.Namespace) -> bool:
        """Apply filters to log entry"""
        if not entry:
            return False
            
        if args.level and entry["level"] != args.level:
            return False
            
        if args.since:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time < self.parse_time(args.since):
                return False
                
        if args.contains and args.contains.lower() not in entry["message"].lower():
            return False
            
        if args.pattern and not re.search(args.pattern, entry["message"]):
            return False
            
        return True
        
    def print_entry(self, entry: dict):
        """Print a log entry"""
        if entry:
            print(f"[{entry['timestamp']}] {entry['level']}: {entry['message']}")
        
    def view_logs(self, phone_number: str, args: argparse.Namespace):
        """View logs for a specific phone number"""
        log_file = self.get_phone_logs(phone_number) / "consolidated.log"
        
        with open(log_file) as f:
            for line in f:
                entry = self.parse_log_line(line)
                if self.filter_log(entry, args):
                    self.print_entry(entry)
                    
    def follow_logs(self, phone_number: str, args: argparse.Namespace):
        """Follow logs in real-time"""
        log_file = self.get_phone_logs(phone_number) / "consolidated.log"
        
        with open(log_file) as f:
            # First, read existing content
            for line in f:
                entry = self.parse_log_line(line)
                if self.filter_log(entry, args):
                    self.print_entry(entry)
            
            # Then follow new content
            while True:
                line = f.readline()
                if line:
                    entry = self.parse_log_line(line)
                    if self.filter_log(entry, args):
                        self.print_entry(entry)
                else:
                    time.sleep(0.1)
                    
    def search_logs(self, phone_number: str, args: argparse.Namespace):
        """Search logs for a specific phone number"""
        log_file = self.get_phone_logs(phone_number) / "consolidated.log"
        
        with open(log_file) as f:
            for line in f:
                entry = self.parse_log_line(line)
                if self.filter_log(entry, args):
                    self.print_entry(entry)
                    
    def summary_logs(self, phone_number: str, args: argparse.Namespace):
        """Summary logs for a specific phone number"""
        log_file = self.get_phone_logs(phone_number) / "consolidated.log"
        
        with open(log_file) as f:
            for line in f:
                entry = self.parse_log_line(line)
                if self.filter_log(entry, args):
                    self.print_entry(entry)
                    
def main():
    parser = argparse.ArgumentParser(description="Anchor Log Analysis Tool")
    parser.add_argument("command", choices=["view", "follow", "search", "summary"])
    parser.add_argument("phone_number", help="Phone number to analyze")
    
    # Filter options
    parser.add_argument("--level", choices=["INFO", "WARNING", "ERROR"])
    parser.add_argument("--since", help="Show logs since (e.g., '2h ago', '2025-01-13')")
    parser.add_argument("--contains", help="Filter by message content")
    parser.add_argument("--pattern", help="Filter by regex pattern")
    
    args = parser.parse_args()
    analyzer = LogAnalyzer()
    
    if args.command == "view":
        analyzer.view_logs(args.phone_number, args)
    elif args.command == "follow":
        analyzer.follow_logs(args.phone_number, args)
    elif args.command == "search":
        analyzer.search_logs(args.phone_number, args)
    elif args.command == "summary":
        analyzer.summary_logs(args.phone_number, args)
    
if __name__ == "__main__":
    main()