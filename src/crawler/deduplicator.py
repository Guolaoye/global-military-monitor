"""去重器"""
from datetime import datetime
from typing import Optional

class Deduplicator:
    """去重器 - 基于 (unit_id + event_type + timestamp) 去重"""
    
    def __init__(self):
        self.seen = set()
    
    def is_duplicate(self, unit_id: str, event_type: str, timestamp: datetime) -> bool:
        """
        检查是否重复
        
        Returns:
            True if duplicate, False otherwise
        """
        key = (unit_id, event_type, timestamp.isoformat())
        if key in self.seen:
            return True
        self.seen.add(key)
        return False
    
    def clear(self):
        """清空去重记录"""
        self.seen.clear()
    
    def get_size(self) -> int:
        """获取已记录数量"""
        return len(self.seen)
