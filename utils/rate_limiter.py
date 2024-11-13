from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class RateLimiter:
    """
    速率限制器实现
    用于控制每个用户的通话和短信频率
    """
    
    def __init__(self, max_requests_per_day: int = 100, cleanup_interval: int = 24):
        """
        初始化速率限制器
        
        Args:
            max_requests_per_day (int): 每日最大请求数
            cleanup_interval (int): 清理历史记录的间隔（小时）
        """
        self.max_requests = max_requests_per_day
        self.cleanup_interval = cleanup_interval
        self.requests: Dict[str, List[datetime]] = {}
        self.last_cleanup: Optional[datetime] = None
        self.logger = logging.getLogger(__name__)
        
    def _cleanup_old_records(self) -> None:
        """清理过期的请求记录"""
        try:
            now = datetime.now()
            if (self.last_cleanup and 
                now - self.last_cleanup < timedelta(hours=self.cleanup_interval)):
                return
                
            yesterday = now - timedelta(days=1)
            for number in list(self.requests.keys()):
                # 只保留24小时内的记录
                self.requests[number] = [
                    timestamp for timestamp in self.requests[number]
                    if timestamp > yesterday
                ]
                # 如果没有有效记录，删除该号码的记录
                if not self.requests[number]:
                    del self.requests[number]
                    
            self.last_cleanup = now
            self.logger.debug(f"Cleaned up rate limiting records. Active numbers: {len(self.requests)}")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def can_proceed(self, number: str) -> bool:
        """
        检查给定号码是否可以继续请求
        
        Args:
            number (str): 电话号码
            
        Returns:
            bool: 如果可以继续请求返回True，否则返回False
        """
        if not number:
            self.logger.warning("Empty phone number provided")
            return False
            
        try:
            self._cleanup_old_records()
            
            now = datetime.now()
            today = now.date()
            
            # 如果是新号码，初始化记录
            if number not in self.requests:
                self.requests[number] = []
            
            # 只统计今天的请求
            today_requests = [
                req for req in self.requests[number]
                if req.date() == today
            ]
            
            # 更新该号码的请求记录
            self.requests[number] = today_requests
            
            # 检查是否超过限制
            if len(today_requests) >= self.max_requests:
                self.logger.warning(f"Rate limit exceeded for number: {number}")
                return False
                
            # 记录新的请求
            self.requests[number].append(now)
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            # 发生错误时，为安全起见返回False
            return False
    
    def get_remaining_requests(self, number: str) -> int:
        """
        获取指定号码今天剩余的请求次数
        
        Args:
            number (str): 电话号码
            
        Returns:
            int: 剩余的请求次数
        """
        if not number:
            return 0
            
        try:
            self._cleanup_old_records()
            
            today = datetime.now().date()
            today_requests = [
                req for req in self.requests.get(number, [])
                if req.date() == today
            ]
            
            return max(0, self.max_requests - len(today_requests))
        except Exception as e:
            self.logger.error(f"Error getting remaining requests: {e}")
            return 0
    
    def reset(self, number: Optional[str] = None) -> None:
        """
        重置速率限制记录
        
        Args:
            number (Optional[str]): 指定号码，如果为None则重置所有记录
        """
        try:
            if number:
                if number in self.requests:
                    del self.requests[number]
                    self.logger.info(f"Reset rate limit for number: {number}")
            else:
                self.requests.clear()
                self.logger.info("Reset all rate limits")
        except Exception as e:
            self.logger.error(f"Error resetting rate limits: {e}")