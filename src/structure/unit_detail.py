"""单位详情页"""
from typing import Dict, Optional

class UnitDetailView:
    """单位详情视图"""
    
    def __init__(self):
        self.current_unit = None
    
    def load_unit(self, unit_id: str, unit_data: Dict):
        """加载单位详情"""
        self.current_unit = {
            "unit_id": unit_id,
            "data": unit_data,
        }
    
    def get_display_data(self) -> Dict:
        """获取显示数据"""
        if not self.current_unit:
            return {}
        return self.current_unit.get("data", {})
    
    def clear(self):
        """清空"""
        self.current_unit = None
