"""毁伤计算（兵棋引擎）"""
from typing import Dict, List

class DamageCalculator:
    """毁伤计算器"""
    
    @staticmethod
    def calculate_weapon_effect(weapon_type: str, target_type: str, distance: float) -> float:
        """
        计算武器效果
        
        Args:
            weapon_type: 武器类型
            target_type: 目标类型
            distance: 距离（km）
        Returns:
            float: 毁伤率 (0.0 ~ 1.0)
        """
        # 简化版毁伤计算
        base_effect = {
            "missile": 0.9,
            "artillery": 0.6,
            "air_strike": 0.75,
            "naval": 0.8,
        }.get(weapon_type, 0.5)
        
        # 距离衰减
        distance_factor = max(0.1, 1.0 - (distance / 100.0))
        
        return base_effect * distance_factor
    
    @staticmethod
    def simulate_battle(attacker: Dict, defender: Dict, weapons: List[str]) -> Dict:
        """
        模拟战斗结果
        
        Returns:
            Dict with casualties, damage, outcome
        """
        attack_power = sum(DamageCalculator.calculate_weapon_effect(w, defender.get("type", ""), 50) for w in weapons)
        defense_power = defender.get("defense_power", 0.5)
        
        attacker_loss_rate = defense_power * 0.3
        defender_loss_rate = attack_power * 0.6
        
        return {
            "attacker_loss_rate": min(1.0, attacker_loss_rate),
            "defender_loss_rate": min(1.0, defender_loss_rate),
            "outcome": "attacker_wins" if attack_power > defense_power else "defender_holds"
        }
