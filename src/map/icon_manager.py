"""图标管理（聚合/展开）"""
from typing import Dict, List, Tuple

class IconManager:
    """军事图标管理器"""
    
    def __init__(self):
        # 图标类型映射
        self.icon_types = {
            "army": "🪖",
            "navy": "🚢",
            "air_force": "✈️",
            "rocket_force": "🚀",
            "coast_guard": "🚤",
            "marines": "🏴",
        }
        self.active_icons = {}  # icon_id -> (lat, lng, type, unit_id)
    
    def add_icon(self, icon_id: str, lat: float, lng: float, icon_type: str, unit_id: str = ""):
        """添加图标"""
        self.active_icons[icon_id] = {
            "lat": lat,
            "lng": lng,
            "type": icon_type,
            "unit_id": unit_id,
            "emoji": self.icon_types.get(icon_type, "📍")
        }
    
    def remove_icon(self, icon_id: str):
        """移除图标"""
        if icon_id in self.active_icons:
            del self.active_icons[icon_id]
    
    def get_cluster(self, center_lat: float, center_lng: float, radius_km: float = 50) -> List[str]:
        """获取聚合图标列表（简化版）"""
        # TODO: 实现基于距离的聚合
        return list(self.active_icons.keys())
    
    def clear_all(self):
        """清空所有图标"""
        self.active_icons.clear()
