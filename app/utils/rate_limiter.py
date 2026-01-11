from datetime import datetime, date
from typing import Dict, Tuple

class RateLimiter:
    def __init__(self, daily_limit: int = 50):
        self.daily_limit = daily_limit
        self.usage: Dict[str, Tuple[date, int]] = {}
    
    def check_and_increment(self, user_id: str) -> bool:
        """
        Returns True if request is allowed, False if limit exceeded.
        """
        today = datetime.now().date()
        
        if user_id not in self.usage:
            self.usage[user_id] = (today, 1)
            return True
        
        last_date, count = self.usage[user_id]
        
        if last_date < today:
            # Reset for new day
            self.usage[user_id] = (today, 1)
            return True
        
        if count >= self.daily_limit:
            return False
            
        self.usage[user_id] = (today, count + 1)
        return True
