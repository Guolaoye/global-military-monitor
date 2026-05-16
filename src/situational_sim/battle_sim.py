"""
战斗模拟器 - Battle Simulator
执行单步战斗模拟，计算伤害和结果
"""

import sys
import os
import copy
import logging
import math
from typing import Dict, List, Optional, Any
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)


class BattleSimulator:
    """
    战斗模拟器
    
    功能：
    - 执行单步战斗模拟
    - 计算双方力量对比
    - 应用伤害结果
    - 生成战斗报告
    """
    
    def __init__(self):
        """初始化战斗模拟器"""
        self.last_results = None
        
    def simulate_step(self, units: Dict[str, Dict], weather: Dict = None) -> Dict:
        """
        执行单步战斗模拟
        
        Args:
            units: 单位字典 {unit_id: unit_data}
            weather: 天气数据
            
        Returns:
            模拟结果
        """
        if not units:
            return {
                'events': [],
                'casualties': {},
                'territory_change': {},
                'summary': '无单位可模拟'
            }
        
        # 按阵营分组
        blue_units = [u for u in units.values() 
                      if u.get('side') == 'blue' or u.get('force') == 'blue']
        red_units = [u for u in units.values() 
                     if u.get('side') == 'red' or u.get('force') == 'red']
        
        # 计算力量对比
        force_ratio = self.calculate_force_ratio(blue_units, red_units)
        
        # 计算天气影响
        weather_modifier = 1.0
        if weather:
            weather_modifier = weather.get('combat_modifier', 1.0)
        
        # 执行战斗
        battle_result = self._execute_battle(blue_units, red_units, force_ratio, weather_modifier)
        
        # 应用伤害
        damage_map = battle_result.get('casualties', {})
        updated_units = self._apply_damage(copy.deepcopy(units), damage_map)
        
        # 记录事件
        events = self._generate_events(blue_units, red_units, battle_result)
        
        self.last_results = {
            'force_ratio': force_ratio,
            'battle_result': battle_result,
            'events': events,
            'weather_modifier': weather_modifier
        }
        
        return {
            'events': events,
            'casualties': battle_result.get('casualties', {}),
            'territory_change': battle_result.get('territory_change', {}),
            'force_ratio': force_ratio,
            'weather_modifier': weather_modifier
        }
    
    def calculate_force_ratio(self, side_a: List[Dict], side_b: List[Dict]) -> Dict:
        """
        计算双方力量对比
        
        Args:
            side_a: A方单位列表
            side_b: B方单位列表
            
        Returns:
            力量对比数据
        """
        strength_a = self._calculate_side_strength(side_a)
        strength_b = self._calculate_side_strength(side_b)
        
        total = strength_a + strength_b
        
        return {
            'side_a': {
                'count': len(side_a),
                'strength': strength_a,
                'percentage': (strength_a / total * 100) if total > 0 else 50
            },
            'side_b': {
                'count': len(side_b),
                'strength': strength_b,
                'percentage': (strength_b / total * 100) if total > 0 else 50
            },
            'ratio': strength_a / strength_b if strength_b > 0 else float('inf'),
            'advantage': 'a' if strength_a > strength_b else 'b'
        }
    
    def _calculate_side_strength(self, units: List[Dict]) -> float:
        """计算阵营总强度"""
        total = 0.0
        
        for unit in units:
            # 基础强度
            base_strength = 1.0
            
            # 生命值因素
            health = unit.get('sim_health', unit.get('health', 100))
            health_factor = health / 100.0
            
            # 士气因素
            morale = unit.get('sim_morale', unit.get('morale', 80))
            morale_factor = morale / 100.0
            
            # 单位类型因素
            unit_type = unit.get('type', '').lower()
            type_factor = self._get_type_factor(unit_type)
            
            # 装备等级因素
            equipment_level = unit.get('equipment_level', unit.get('level', 1))
            level_factor = 1.0 + (equipment_level - 1) * 0.1
            
            # 计算综合强度
            unit_strength = (base_strength * health_factor * morale_factor * 
                           type_factor * level_factor)
            
            total += unit_strength
        
        return total
    
    def _get_type_factor(self, unit_type: str) -> float:
        """获取单位类型强度系数"""
        type_factors = {
            'infantry': 1.0,
            'soldier': 1.0,
            'tank': 2.5,
            'armor': 2.5,
            'artillery': 2.0,
            'aircraft': 3.0,
            'plane': 3.0,
            'fighter': 3.5,
            'bomber': 2.5,
            'navy': 3.5,
            'ship': 3.0,
            'submarine': 4.0,
            'missile': 4.5,
            'radar': 0.5,
            'communication': 0.5,
            'logistics': 0.3,
            'support': 0.5
        }
        
        for key, factor in type_factors.items():
            if key in unit_type:
                return factor
        
        return 1.0
    
    def _execute_battle(self, blue_units: List[Dict], red_units: List[Dict],
                        force_ratio: Dict, weather_modifier: float) -> Dict:
        """执行战斗计算"""
        
        # 基础伤害率
        base_damage_rate = 0.1
        
        # 计算蓝方对红方的伤害
        blue_damage = force_ratio['side_a']['strength'] * base_damage_rate * weather_modifier
        # 计算红方对蓝方的伤害
        red_damage = force_ratio['side_b']['strength'] * base_damage_rate * weather_modifier
        
        # 分配伤害
        casualties = {'blue': {}, 'red': {}}
        territory_change = {}
        
        # 蓝方伤亡计算
        for unit in blue_units:
            unit_id = unit.get('sim_id') or unit.get('id', 'unknown')
            damage = red_damage / max(len(blue_units), 1)
            casualties['blue'][unit_id] = {
                'damage': damage,
                'health_before': unit.get('sim_health', 100),
                'health_after': max(0, unit.get('sim_health', 100) - damage),
                'destroyed': False
            }
        
        # 红方伤亡计算
        for unit in red_units:
            unit_id = unit.get('sim_id') or unit.get('id', 'unknown')
            damage = blue_damage / max(len(red_units), 1)
            casualties['red'][unit_id] = {
                'damage': damage,
                'health_before': unit.get('sim_health', 100),
                'health_after': max(0, unit.get('sim_health', 100) - damage),
                'destroyed': False
            }
        
        return {
            'casualties': casualties,
            'territory_change': territory_change,
            'blue_damage_dealt': blue_damage,
            'red_damage_dealt': red_damage,
            'weather_modifier': weather_modifier
        }
    
    def apply_damage(self, units: Dict[str, Dict], damage_map: Dict) -> Dict[str, Dict]:
        """
        应用伤害到单位
        
        Args:
            units: 单位字典
            damage_map: 伤害映射
            
        Returns:
            更新后的单位字典
        """
        updated_units = copy.deepcopy(units)
        
        for side, casualties in damage_map.items():
            for unit_id, damage_info in casualties.items():
                # 查找单位
                for uid, unit in updated_units.items():
                    if (unit.get('sim_id') == unit_id or 
                        str(unit.get('id')) == str(unit_id)):
                        
                        new_health = damage_info['health_after']
                        unit['sim_health'] = new_health
                        
                        # 检查是否摧毁
                        if new_health <= 0:
                            unit['sim_status'] = 'destroyed'
                            damage_info['destroyed'] = True
                        
                        break
        
        return updated_units
    
    def _apply_damage(self, units: Dict[str, Dict], damage_map: Dict) -> Dict[str, Dict]:
        """应用伤害的内部方法"""
        return self.apply_damage(units, damage_map)
    
    def _generate_events(self, blue_units: List[Dict], red_units: List[Dict],
                        battle_result: Dict) -> List[Dict]:
        """生成战斗事件"""
        events = []
        casualties = battle_result.get('casualties', {})
        
        # 记录伤亡事件
        for side, unit_casualties in casualties.items():
            for unit_id, info in unit_casualties.items():
                if info['damage'] > 0:
                    events.append({
                        'type': 'damage',
                        'side': side,
                        'unit_id': unit_id,
                        'damage': info['damage'],
                        'remaining_health': info['health_after'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if info['health_after'] <= 0:
                        events.append({
                            'type': 'unit_destroyed',
                            'side': side,
                            'unit_id': unit_id,
                            'timestamp': datetime.now().isoformat()
                        })
        
        # 记录力量变化
        force_ratio = battle_result.get('force_ratio', {})
        if force_ratio:
            events.append({
                'type': 'force_change',
                'blue_strength': force_ratio.get('side_a', {}).get('strength', 0),
                'red_strength': force_ratio.get('side_b', {}).get('strength', 0),
                'timestamp': datetime.now().isoformat()
            })
        
        return events
    
    def generate_report(self) -> str:
        """生成战斗报告文本"""
        if not self.last_results:
            return "无战斗记录"
        
        lines = []
        lines.append("=" * 60)
        lines.append("战斗模拟报告")
        lines.append("=" * 60)
        
        force_ratio = self.last_results.get('force_ratio', {})
        lines.append(f"蓝方单位数: {force_ratio.get('side_a', {}).get('count', 0)}")
        lines.append(f"蓝方强度: {force_ratio.get('side_a', {}).get('strength', 0):.2f}")
        lines.append(f"红方单位数: {force_ratio.get('side_b', {}).get('count', 0)}")
        lines.append(f"红方强度: {force_ratio.get('side_b', {}).get('strength', 0):.2f}")
        lines.append(f"力量对比: {force_ratio.get('ratio', 0):.2f}")
        lines.append(f"天气修正: {self.last_results.get('weather_modifier', 1.0):.2f}")
        
        lines.append("")
        lines.append("伤亡情况:")
        casualties = self.last_results.get('battle_result', {}).get('casualties', {})
        
        blue_cas = casualties.get('blue', {})
        red_cas = casualties.get('red', {})
        
        blue_total = sum(c.get('damage', 0) for c in blue_cas.values())
        red_total = sum(c.get('damage', 0) for c in red_cas.values())
        
        lines.append(f"  蓝方总伤害: {blue_total:.2f}")
        lines.append(f"  红方总伤害: {red_total:.2f}")
        
        lines.append("")
        lines.append("最近事件:")
        for event in self.last_results.get('events', [])[-5:]:
            lines.append(f"  [{event.get('type')}] {event}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def simulate_engagement(self, attacker_units: List[Dict], 
                           defender_units: List[Dict],
                           engagement_type: str = 'ground') -> Dict:
        """
        模拟特定交战
        
        Args:
            attacker_units: 攻击方单位
            defender_units: 防御方单位
            engagement_type: 交战类型 (ground/air/naval)
            
        Returns:
            交战结果
        """
        # 根据交战类型调整参数
        type_modifiers = {
            'ground': {'attacker_bonus': 1.0, 'defender_bonus': 1.2},
            'air': {'attacker_bonus': 1.2, 'defender_bonus': 0.9},
            'naval': {'attacker_bonus': 1.1, 'defender_bonus': 1.0}
        }
        
        modifiers = type_modifiers.get(engagement_type, type_modifiers['ground'])
        
        # 计算双方强度
        attacker_strength = self._calculate_side_strength(attacker_units) * modifiers['attacker_bonus']
        defender_strength = self._calculate_side_strength(defender_units) * modifiers['defender_bonus']
        
        # 计算战损
        attacker_loss_rate = defender_strength / (attacker_strength + defender_strength) * 0.3
        defender_loss_rate = attacker_strength / (attacker_strength + defender_strength) * 0.4
        
        return {
            'attacker_strength': attacker_strength,
            'defender_strength': defender_strength,
            'attacker_loss_rate': attacker_loss_rate,
            'defender_loss_rate': defender_loss_rate,
            'winner': 'attacker' if attacker_strength > defender_strength * 1.2 else 'defender',
            'engagement_type': engagement_type
        }


def create_battle_simulator() -> BattleSimulator:
    """创建战斗模拟器实例"""
    return BattleSimulator()


if __name__ == '__main__':
    simulator = BattleSimulator()
    
    # 测试用样例单位
    test_units = {
        'blue_1': {'sim_id': 'blue_1', 'side': 'blue', 'type': 'tank', 
                   'sim_health': 100, 'sim_morale': 80},
        'blue_2': {'sim_id': 'blue_2', 'side': 'blue', 'type': 'infantry',
                   'sim_health': 90, 'sim_morale': 85},
        'red_1': {'sim_id': 'red_1', 'side': 'red', 'type': 'tank',
                  'sim_health': 95, 'sim_morale': 75},
    }
    
    result = simulator.simulate_step(test_units)
    print("战斗模拟测试:")
    print(f"  事件数: {len(result['events'])}")
    print(f"  力量对比: {result['force_ratio']}")