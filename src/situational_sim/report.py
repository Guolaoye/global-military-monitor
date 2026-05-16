"""
模拟报告生成器 - Simulation Report Generator
生成战斗模拟报告和地图快照
"""

import sys
import os
import json
import copy
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)


class SimulationReport:
    """
    模拟报告生成器
    
    功能：
    - 生成文字战斗报告
    - 导出地图快照元数据
    - 汇总模拟结果统计
    """
    
    def __init__(self):
        """初始化报告生成器"""
        self.report_template = {
            'header': '=' * 60,
            'title': '模拟情境报告',
            'sections': ['overview', 'force_analysis', 'battle_events', 'casualties', 'conclusion']
        }
    
    def generate(self, units_before: Dict[str, Dict], 
                 units_after: Dict[str, Dict],
                 events: List[Dict]) -> Dict:
        """
        生成完整模拟报告
        
        Args:
            units_before: 模拟前的单位状态
            units_after: 模拟后的单位状态
            events: 模拟过程中的事件列表
            
        Returns:
            报告字典
        """
        # 基本信息
        report = {
            'timestamp': datetime.now().isoformat(),
            'sim_status': 'completed',
            'overview': self._generate_overview(units_before, units_after, events),
            'force_analysis': self._analyze_forces(units_before, units_after),
            'battle_events': self._process_events(events),
            'casualties': self._calculate_casualties(units_before, units_after),
            'territory_change': self._analyze_territory_change(units_before, units_after),
            'recommendations': self._generate_recommendations(units_after, events)
        }
        
        return report
    
    def _generate_overview(self, units_before: Dict, units_after: Dict, 
                          events: List) -> Dict:
        """生成概览"""
        blue_before = self._count_by_side(units_before, 'blue')
        blue_after = self._count_by_side(units_after, 'blue')
        red_before = self._count_by_side(units_before, 'red')
        red_after = self._count_by_side(units_after, 'red')
        
        return {
            'total_units_before': len(units_before),
            'total_units_after': len(units_after),
            'blue_units': {'before': blue_before, 'after': blue_after},
            'red_units': {'before': red_before, 'after': red_after},
            'events_count': len(events),
            'steps_completed': max([e.get('step', 0) for e in events] or [0])
        }
    
    def _count_by_side(self, units: Dict, side: str) -> int:
        """按阵营计数"""
        return len([u for u in units.values() 
                   if u.get('side') == side or u.get('force') == side])
    
    def _analyze_forces(self, units_before: Dict, units_after: Dict) -> Dict:
        """分析双方力量"""
        blue_before = self._calculate_strength([u for u in units_before.values() 
                                                 if u.get('side') == 'blue' or u.get('force') == 'blue'])
        blue_after = self._calculate_strength([u for u in units_after.values()
                                               if u.get('side') == 'blue' or u.get('force') == 'blue'])
        red_before = self._calculate_strength([u for u in units_before.values()
                                              if u.get('side') == 'red' or u.get('force') == 'red'])
        red_after = self._calculate_strength([u for u in units_after.values()
                                            if u.get('side') == 'red' or u.get('force') == 'red'])
        
        return {
            'blue': {'initial': blue_before, 'final': blue_after, 
                    'change': blue_after - blue_before},
            'red': {'initial': red_before, 'final': red_after,
                   'change': red_after - red_before},
            'ratio_before': blue_before / red_before if red_before > 0 else float('inf'),
            'ratio_after': blue_after / red_after if red_after > 0 else float('inf')
        }
    
    def _calculate_strength(self, units: List[Dict]) -> float:
        """计算阵营总强度"""
        total = 0.0
        for unit in units:
            health = unit.get('sim_health', unit.get('health', 100)) / 100.0
            morale = unit.get('sim_morale', unit.get('morale', 80)) / 100.0
            type_factor = self._get_type_factor(unit.get('type', ''))
            
            total += 1.0 * health * morale * type_factor
        
        return total
    
    def _get_type_factor(self, unit_type: str) -> float:
        """获取单位类型系数"""
        type_factors = {
            'infantry': 1.0, 'soldier': 1.0,
            'tank': 2.5, 'armor': 2.5,
            'artillery': 2.0,
            'aircraft': 3.0, 'plane': 3.0,
            'navy': 3.5, 'ship': 3.0,
            'missile': 4.5
        }
        
        unit_type = unit_type.lower()
        for key, factor in type_factors.items():
            if key in unit_type:
                return factor
        return 1.0
    
    def _process_events(self, events: List[Dict]) -> List[Dict]:
        """处理事件列表"""
        processed = []
        
        for event in events:
            processed_event = {
                'timestamp': event.get('timestamp', ''),
                'type': event.get('type', 'unknown'),
                'step': event.get('step', 0),
                'details': event.get('details', {})
            }
            
            # 事件类型分类
            if event.get('type') == 'unit_destroyed':
                processed_event['summary'] = f"单位 {event.get('unit_id')} 被摧毁"
            elif event.get('type') == 'damage':
                processed_event['summary'] = f"单位 {event.get('unit_id')} 受到 {event.get('damage', 0):.1f} 点伤害"
            elif event.get('type') == 'force_change':
                processed_event['summary'] = f"力量变化: 蓝 {event.get('blue_strength', 0):.1f} vs 红 {event.get('red_strength', 0):.1f}"
            
            processed.append(processed_event)
        
        return processed
    
    def _calculate_casualties(self, units_before: Dict, units_after: Dict) -> Dict:
        """计算伤亡情况"""
        casualties = {'blue': {}, 'red': {}}
        
        for unit_id, unit_before in units_before.items():
            side = unit_before.get('side') or unit_before.get('force', 'unknown')
            unit_after = units_after.get(unit_id)
            
            if not unit_after:
                # 单位被摧毁
                casualties[side][unit_id] = {
                    'destroyed': True,
                    'health_lost': unit_before.get('sim_health', unit_before.get('health', 100))
                }
            else:
                health_before = unit_before.get('sim_health', unit_before.get('health', 100))
                health_after = unit_after.get('sim_health', 100)
                
                if health_after < health_before:
                    casualties[side][unit_id] = {
                        'destroyed': False,
                        'health_lost': health_before - health_after
                    }
        
        # 统计汇总
        blue_destroyed = sum(1 for c in casualties.get('blue', {}).values() if c.get('destroyed'))
        red_destroyed = sum(1 for c in casualties.get('red', {}).values() if c.get('destroyed'))
        
        return {
            'details': casualties,
            'summary': {
                'blue': {
                    'units_lost': blue_destroyed,
                    'total_damage': sum(c.get('health_lost', 0) for c in casualties.get('blue', {}).values())
                },
                'red': {
                    'units_lost': red_destroyed,
                    'total_damage': sum(c.get('health_lost', 0) for c in casualties.get('red', {}).values())
                }
            }
        }
    
    def _analyze_territory_change(self, units_before: Dict, units_after: Dict) -> Dict:
        """分析领土变化"""
        changes = {
            'gained': [],
            'lost': [],
            'contested': []
        }
        
        # 简化的领土分析：检查单位位置变化
        for unit_id in units_after:
            unit_after = units_after[unit_id]
            unit_before = units_before.get(unit_id)
            
            if unit_before:
                pos_after = unit_after.get('sim_position', {})
                pos_before = unit_before.get('sim_position', {})
                
                # 计算位置差异
                lat_diff = abs(pos_after.get('lat', 0) - pos_before.get('lat', 0))
                lng_diff = abs(pos_after.get('lng', 0) - pos_before.get('lng', 0))
                
                if lat_diff > 0.5 or lng_diff > 0.5:
                    changes['contested'].append(unit_id)
        
        return changes
    
    def _generate_recommendations(self, units_after: Dict, events: List[Dict]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 分析当前态势
        blue_strength = self._calculate_strength([u for u in units_after.values() 
                                                   if u.get('side') == 'blue' or u.get('force') == 'blue'])
        red_strength = self._calculate_strength([u for u in units_after.values()
                                                 if u.get('side') == 'red' or u.get('force') == 'red'])
        
        ratio = blue_strength / red_strength if red_strength > 0 else float('inf')
        
        if ratio > 1.5:
            recommendations.append("蓝方占据优势，建议发起进攻行动")
        elif ratio > 1.0:
            recommendations.append("蓝方略占优势，建议巩固阵地并准备进攻")
        elif ratio > 0.5:
            recommendations.append("红方占据优势，建议转入防御姿态")
        else:
            recommendations.append("态势不利，建议保存实力，等待增援")
        
        # 检查损坏严重的单位
        damaged_units = [u.get('sim_id', u.get('id')) for u in units_after.values()
                        if u.get('sim_health', 100) < 30]
        if damaged_units:
            recommendations.append(f"以下单位需要维修: {', '.join(damaged_units[:5])}")
        
        return recommendations
    
    def export_map_snapshot(self, config: Dict = None) -> Dict:
        """
        导出地图快照元数据
        
        Args:
            config: 地图配置
            
        Returns:
            地图快照数据
        """
        if not config:
            config = {}
        
        return {
            'timestamp': datetime.now().isoformat(),
            'format': 'map_snapshot',
            'bounds': config.get('bounds', {
                'min_lat': -90, 'max_lat': 90,
                'min_lng': -180, 'max_lng': 180
            }),
            'zoom': config.get('zoom', 10),
            'layers': ['units', 'territory', 'weather'],
            'export_path': config.get('export_path', 'exports/map_snapshots/')
        }
    
    def generate_text_report(self, report: Dict) -> str:
        """生成文本格式报告"""
        lines = []
        
        lines.append('=' * 60)
        lines.append('模拟情境报告 - Simulation Report')
        lines.append('=' * 60)
        lines.append('')
        
        # 时间戳
        lines.append(f"生成时间: {report.get('timestamp', 'N/A')}")
        lines.append(f"模拟状态: {report.get('sim_status', 'unknown')}")
        lines.append('')
        
        # 概览
        overview = report.get('overview', {})
        lines.append('【概览】')
        lines.append(f"  总单位数: {overview.get('total_units_before', 0)} -> {overview.get('total_units_after', 0)}")
        lines.append(f"  蓝方: {overview.get('blue_units', {}).get('before', 0)} -> {overview.get('blue_units', {}).get('after', 0)}")
        lines.append(f"  红方: {overview.get('red_units', {}).get('before', 0)} -> {overview.get('red_units', {}).get('after', 0)}")
        lines.append(f"  事件数: {overview.get('events_count', 0)}")
        lines.append('')
        
        # 力量分析
        force = report.get('force_analysis', {})
        lines.append('【力量分析】')
        lines.append(f"  蓝方: {force.get('blue', {}).get('initial', 0):.1f} -> {force.get('blue', {}).get('final', 0):.1f} (变化: {force.get('blue', {}).get('change', 0):+.1f})")
        lines.append(f"  红方: {force.get('red', {}).get('initial', 0):.1f} -> {force.get('red', {}).get('final', 0):.1f} (变化: {force.get('red', {}).get('change', 0):+.1f})")
        lines.append(f"  力量比: {force.get('ratio_before', 0):.2f} -> {force.get('ratio_after', 0):.2f}")
        lines.append('')
        
        # 伤亡
        casualties = report.get('casualties', {}).get('summary', {})
        lines.append('【伤亡情况】')
        lines.append(f"  蓝方损失: {casualties.get('blue', {}).get('units_lost', 0)} 单位, {casualties.get('blue', {}).get('total_damage', 0):.1f} 生命值")
        lines.append(f"  红方损失: {casualties.get('red', {}).get('units_lost', 0)} 单位, {casualties.get('red', {}).get('total_damage', 0):.1f} 生命值")
        lines.append('')
        
        # 建议
        recommendations = report.get('recommendations', [])
        if recommendations:
            lines.append('【行动建议】')
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"  {i}. {rec}")
            lines.append('')
        
        # 关键事件
        events = report.get('battle_events', [])
        if events:
            lines.append('【关键事件】')
            key_events = [e for e in events if e.get('type') in ['unit_destroyed', 'damage']]
            for event in key_events[:10]:
                lines.append(f"  [{event.get('step', 0)}] {event.get('summary', '')}")
            lines.append('')
        
        lines.append('=' * 60)
        
        return '\n'.join(lines)
    
    def export_json(self, report: Dict, pretty: bool = True) -> str:
        """导出JSON格式报告"""
        if pretty:
            return json.dumps(report, ensure_ascii=False, indent=2)
        return json.dumps(report, ensure_ascii=False)
    
    def export_csv(self, report: Dict) -> str:
        """导出CSV格式报告（用于电子表格）"""
        lines = []
        
        # 表头
        lines.append("单位ID,阵营,类型,生命值,士气,状态")
        
        # 单位数据
        casualties = report.get('casualties', {}).get('details', {})
        for side, units in casualties.items():
            for unit_id, data in units.items():
                lines.append(f"{unit_id},{side},,,,{data.get('destroyed', False) and 'destroyed' or 'active'}")
        
        return '\n'.join(lines)


def create_report_generator() -> SimulationReport:
    """创建报告生成器实例"""
    return SimulationReport()


if __name__ == '__main__':
    report_gen = SimulationReport()
    
    # 测试数据
    test_before = {
        'unit1': {'id': 'unit1', 'side': 'blue', 'type': 'tank', 'sim_health': 100, 'sim_morale': 80},
        'unit2': {'id': 'unit2', 'side': 'red', 'type': 'infantry', 'sim_health': 100, 'sim_morale': 75}
    }
    test_after = {
        'unit1': {'id': 'unit1', 'side': 'blue', 'type': 'tank', 'sim_health': 70, 'sim_morale': 75},
        'unit2': {'id': 'unit2', 'side': 'red', 'type': 'infantry', 'sim_health': 30, 'sim_morale': 40}
    }
    test_events = [
        {'type': 'damage', 'step': 1, 'unit_id': 'unit1', 'damage': 30, 'timestamp': '2024-01-01T10:00:00'},
        {'type': 'unit_destroyed', 'step': 2, 'unit_id': 'unit2', 'timestamp': '2024-01-01T10:05:00'}
    ]
    
    report = report_gen.generate(test_before, test_after, test_events)
    print("报告生成成功:")
    print(report_gen.generate_text_report(report))