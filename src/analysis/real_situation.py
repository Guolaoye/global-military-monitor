"""真实态势推演"""
from typing import List, Dict
from datetime import datetime

class RealSituationAnalyzer:
    """真实态势分析器"""
    
    def __init__(self):
        self.timeline = []
    
    def add_event(self, unit_id: str, event_type: str, timestamp: datetime, data: Dict):
        """添加事件到时间轴"""
        self.timeline.append({
            "unit_id": unit_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "data": data
        })
    
    def get_timeline(self, unit_id: str = None) -> List[Dict]:
        """获取时间轴（可按 unit_id 筛选）"""
        if unit_id:
            return [e for e in self.timeline if e["unit_id"] == unit_id]
        return self.timeline
    
    def get_unit_positions(self, unit_id: str) -> List[Dict]:
        """获取单位历史位置"""
        return [
            {"lat": e["data"].get("lat"), "lng": e["data"].get("lng"), "time": e["timestamp"]}
            for e in self.timeline
            if e["unit_id"] == unit_id and "lat" in e["data"]
        ]
    
    def clear(self):
        """清空时间轴"""
        self.timeline.clear()
