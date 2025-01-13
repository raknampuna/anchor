from datetime import date, timedelta
from redis import Redis, ConnectionError
import json
from typing import Dict, Optional

class RedisStorage:
    def __init__(self, redis_url: str):
        """Initialize Redis connection"""
        try:
            self.redis = Redis.from_url(redis_url)
            self.redis.ping()  # Test connection
        except ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    def save_context(self, user_id: str, context: dict) -> bool:
        """Save user context to Redis"""
        try:
            key = f"user:{user_id}:date:{date.today()}"
            # Convert all values to strings for Redis storage
            context_str = {k: json.dumps(v) for k, v in context.items()}
            return self.redis.hmset(key, context_str)
        except Exception as e:
            print(f"Error saving context: {str(e)}")
            return False

    def get_context(self, user_id: str) -> Optional[Dict]:
        """Get user context from Redis"""
        try:
            key = f"user:{user_id}:date:{date.today()}"
            context = self.redis.hgetall(key)
            if not context:
                return None
            # Convert stored strings back to Python objects
            return {k.decode(): json.loads(v.decode()) for k, v in context.items()}
        except Exception as e:
            print(f"Error getting context: {str(e)}")
            return None

    def cleanup_old_contexts(self, days: int = 7) -> int:
        """Cleanup contexts older than specified days"""
        try:
            pattern = "user:*:date:*"
            deleted = 0
            cutoff_date = date.today() - timedelta(days=days)
            
            for key in self.redis.scan_iter(pattern):
                key_str = key.decode()
                key_date_str = key_str.split(":")[-1]
                try:
                    key_date = date.fromisoformat(key_date_str)
                    if key_date < cutoff_date:
                        self.redis.delete(key)
                        deleted += 1
                except ValueError:
                    continue
            return deleted
        except Exception as e:
            print(f"Error cleaning up contexts: {str(e)}")
            return 0