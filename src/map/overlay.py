"""叠加层（图标/轨迹/热力图）"""
from typing import List, Dict

class OverlayManager:
    """叠加层管理器"""
    
    def __init__(self):
        self.layers = {
            "icons": [],
            "tracks": [],
            "heatmaps": [],
        }
        self.visible = {
            "icons": True,
            "tracks": True,
            "heatmaps": False,
        }
    
    def add_icon_layer(self, icons: List[Dict]):
        """添加图标层"""
        self.layers["icons"] = icons
    
    def add_track_layer(self, tracks: List[Dict]):
        """添加轨迹层"""
        self.layers["tracks"] = tracks
    
    def add_heatmap_layer(self, heatmaps: List[Dict]):
        """添加热力图层"""
        self.layers["heatmaps"] = heatmaps
    
    def set_layer_visible(self, layer_name: str, visible: bool):
        """设置图层可见性"""
        if layer_name in self.visible:
            self.visible[layer_name] = visible
    
    def get_visible_layers(self) -> Dict[str, bool]:
        """获取可见性状态"""
        return self.visible.copy()
    
    def clear_all(self):
        """清空所有叠加层"""
        for key in self.layers:
            self.layers[key] = []
