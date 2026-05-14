"""模拟态势推演"""
from typing import Dict, List
import copy

class SimSituationEngine:
    """模拟态势推演引擎"""
    
    def __init__(self):
        self.simulation_units = {}
        self.original_units = {}
    
    def clone_unit(self, unit_id: str, unit_data: Dict):
        """复制单位用于模拟"""
        self.original_units[unit_id] = copy.deepcopy(unit_data)
        self.simulation_units[unit_id] = copy.deepcopy(unit_data)
    
    def update_unit_param(self, unit_id: str, param: str, value):
        """更新模拟单位参数"""
        if unit_id in self.simulation_units:
            self.simulation_units[unit_id][param] = value
    
    def run_simulation(self, steps: int = 10) -> List[Dict]:
        """运行模拟推演"""
        # 占位：实际模拟引擎
        results = []
        for step in range(steps):
            results.append({
                "step": step,
                "units": copy.deepcopy(self.simulation_units)
            })
        return results
    
    def reset_unit(self, unit_id: str):
        """重置单位到原始状态"""
        if unit_id in self.original_units:
            self.simulation_units[unit_id] = copy.deepcopy(self.original_units[unit_id])
    
    def clear_simulation(self):
        """清空模拟"""
        self.simulation_units.clear()
        self.original_units.clear()
