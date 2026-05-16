"""
模拟单位管理器 - Simulated Unit Manager
管理模拟中的单位生命周期，支持从DB加载和临时添加
"""

import sys
import os
import copy
import logging
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)


class SimUnitManager:
    """
    模拟单位管理器
    
    功能：
    - 从数据库加载真实单位作为模拟基础
    - 管理临时添加的模拟单位
    - 提供单位查询和操作接口
    - 支持重置到原始状态
    """
    
    def __init__(self, db_path: str = None):
        """初始化单位管理器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or self._get_default_db_path()
        self._units = {}           # 当前模拟单位
        self._original_units = {}  # 原始单位数据（用于重置）
        self._temp_units = set()   # 临时单位ID集合
    
    def _get_default_db_path(self) -> str:
        """获取默认数据库路径"""
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        return os.path.join(project_root, 'data', 'military_monitor.db')
    
    def load_from_db(self) -> Dict[str, Dict]:
        """从数据库加载单位数据
        
        Returns:
            加载的单位字典
        """
        logger.info("从数据库加载单位数据...")
        
        units = self._fetch_all_units()
        
        # 保存原始副本
        self._original_units = copy.deepcopy(units)
        
        # 初始化当前单位
        self._units = copy.deepcopy(units)
        
        # 标记临时单位为空
        self._temp_units = set()
        
        logger.info(f"已加载 {len(units)} 个单位")
        return units
    
    def _fetch_all_units(self) -> Dict[str, Dict]:
        """从数据库获取所有单位"""
        units = {}
        
        try:
            import sqlite3
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                table_names = ['units', 'military_units', 'unit_positions']
                
                for table in table_names:
                    try:
                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                            (table,)
                        )
                        if cursor.fetchone():
                            cursor.execute(f"SELECT * FROM {table}")
                            cols = [desc[0] for desc in cursor.description]
                            rows = cursor.fetchall()
                            
                            for row in rows:
                                row_dict = dict(zip(cols, row))
                                unit_id = row_dict.get('id') or row_dict.get('unit_id')
                                if unit_id:
                                    units[str(unit_id)] = row_dict
                    except Exception:
                        continue
                
                conn.close()
                
        except Exception as e:
            logger.warning(f"数据库读取失败: {e}")
        
        return units
    
    def add_unit(self, unit_data: Dict) -> str:
        """
        添加单位到模拟
        
        Args:
            unit_data: 单位数据
            
        Returns:
            添加的单位ID
        """
        unit_id = unit_data.get('id') or unit_data.get('unit_id') or unit_data.get('sim_id')
        
        if not unit_id:
            # 生成临时ID
            unit_id = f"temp_{len(self._units)}_{id(unit_data)}"
        
        unit_id_str = str(unit_id)
        
        # 深拷贝数据
        unit_copy = copy.deepcopy(unit_data)
        unit_copy['sim_id'] = unit_copy.get('sim_id') or unit_id_str
        unit_copy['is_temp_unit'] = unit_data.get('is_temp_unit', False)
        
        # 添加模拟属性
        unit_copy['sim_health'] = unit_copy.get('sim_health', unit_copy.get('health', 100))
        unit_copy['sim_morale'] = unit_copy.get('sim_morale', unit_copy.get('morale', 80))
        unit_copy['sim_status'] = unit_copy.get('sim_status', 'active')
        
        # 初始化位置
        if 'sim_position' not in unit_copy:
            unit_copy['sim_position'] = {
                'lat': unit_copy.get('latitude') or unit_copy.get('lat', 0),
                'lng': unit_copy.get('longitude') or unit_copy.get('lng', 0)
            }
        
        # 添加到存储
        self._units[unit_id_str] = unit_copy
        
        # 标记临时单位
        if unit_copy.get('is_temp_unit', False):
            self._temp_units.add(unit_id_str)
        
        logger.debug(f"添加单位: {unit_id_str}")
        return unit_id_str
    
    def remove_unit(self, unit_id: str) -> bool:
        """
        从模拟中移除单位
        
        Args:
            unit_id: 单位ID
            
        Returns:
            是否成功
        """
        unit_id_str = str(unit_id)
        
        if unit_id_str in self._units:
            # 检查是否是临时单位
            if unit_id_str in self._temp_units:
                self._temp_units.discard(unit_id_str)
            
            del self._units[unit_id_str]
            logger.info(f"移除单位: {unit_id_str}")
            return True
        
        return False
    
    def get_unit(self, unit_id: str) -> Optional[Dict]:
        """获取指定单位"""
        return self._units.get(str(unit_id))
    
    def get_units(self, side: str = None, status: str = None) -> List[Dict]:
        """
        获取单位列表
        
        Args:
            side: 过滤阵营（blue/red）
            status: 过滤状态
            
        Returns:
            单位列表
        """
        units = list(self._units.values())
        
        if side:
            units = [u for u in units if u.get('side') == side or u.get('force') == side]
        
        if status:
            units = [u for u in units if u.get('sim_status') == status]
        
        return units
    
    def get_all_units(self) -> List[Dict]:
        """获取所有单位"""
        return list(self._units.values())
    
    def get_unit_count(self, side: str = None) -> int:
        """获取单位数量"""
        if side:
            return len([u for u in self._units.values() if u.get('side') == side or u.get('force') == side])
        return len(self._units)
    
    def get_temp_unit_ids(self) -> List[str]:
        """获取所有临时单位ID"""
        return list(self._temp_units)
    
    def update_unit(self, unit_id: str, updates: Dict) -> bool:
        """
        更新单位数据
        
        Args:
            unit_id: 单位ID
            updates: 更新数据
            
        Returns:
            是否成功
        """
        unit_id_str = str(unit_id)
        
        if unit_id_str not in self._units:
            logger.warning(f"单位 {unit_id} 不存在")
            return False
        
        # 更新模拟属性
        for key, value in updates.items():
            self._units[unit_id_str][key] = value
            
            # 同步sim_前缀属性
            if key in ['health', 'morale', 'position', 'status']:
                self._units[unit_id_str][f'sim_{key}'] = value
                
                if key == 'position':
                    self._units[unit_id_str]['sim_position'] = value
        
        logger.debug(f"更新单位 {unit_id}: {updates}")
        return True
    
    def update_unit_health(self, unit_id: str, health: float) -> bool:
        """更新单位生命值"""
        return self.update_unit(unit_id, {'sim_health': health, 'health': health})
    
    def update_unit_position(self, unit_id: str, lat: float, lng: float) -> bool:
        """更新单位位置"""
        return self.update_unit(unit_id, {
            'sim_position': {'lat': lat, 'lng': lng},
            'latitude': lat,
            'longitude': lng
        })
    
    def update_unit_morale(self, unit_id: str, morale: float) -> bool:
        """更新单位士气"""
        return self.update_unit(unit_id, {'sim_morale': morale, 'morale': morale})
    
    def update_unit_status(self, unit_id: str, status: str) -> bool:
        """更新单位状态"""
        return self.update_unit(unit_id, {'sim_status': status, 'status': status})
    
    def apply_damage(self, unit_id: str, damage: float) -> Dict:
        """
        对单位应用伤害
        
        Args:
            unit_id: 单位ID
            damage: 伤害值
            
        Returns:
            伤害结果
        """
        unit = self.get_unit(unit_id)
        if not unit:
            return {'success': False, 'message': '单位不存在'}
        
        current_health = unit.get('sim_health', 100)
        new_health = max(0, current_health - damage)
        
        self.update_unit_health(unit_id, new_health)
        
        result = {
            'success': True,
            'unit_id': unit_id,
            'damage': damage,
            'health_before': current_health,
            'health_after': new_health,
            'destroyed': new_health <= 0
        }
        
        if result['destroyed']:
            self.update_unit_status(unit_id, 'destroyed')
        
        return result
    
    def reset_to_original(self):
        """
        重置到原始状态 - 丢弃所有模拟修改
        
        从原始数据副本恢复，移除所有临时单位
        """
        logger.info("重置单位管理器到原始状态...")
        
        # 恢复原始数据
        self._units = copy.deepcopy(self._original_units)
        
        # 清除临时单位标记
        self._temp_units = set()
        
        logger.info(f"已重置，共 {len(self._units)} 个单位")
    
    def reset_unit(self, unit_id: str) -> bool:
        """
        重置单个单位到原始状态
        
        Args:
            unit_id: 单位ID
            
        Returns:
            是否成功
        """
        unit_id_str = str(unit_id)
        
        # 移除临时单位
        if unit_id_str in self._temp_units:
            self._temp_units.discard(unit_id_str)
            if unit_id_str in self._units:
                del self._units[unit_id_str]
            return True
        
        # 恢复原始状态
        if unit_id_str in self._original_units:
            self._units[unit_id_str] = copy.deepcopy(self._original_units[unit_id_str])
            return True
        
        return False
    
    def get_sides(self) -> Dict[str, List[Dict]]:
        """按阵营分组获取单位"""
        sides = {'blue': [], 'red': [], 'unknown': []}
        
        for unit in self._units.values():
            side = unit.get('side') or unit.get('force') or 'unknown'
            
            if side == 'blue':
                sides['blue'].append(unit)
            elif side == 'red':
                sides['red'].append(unit)
            else:
                sides['unknown'].append(unit)
        
        return sides
    
    def calculate_force_ratio(self) -> Dict:
        """计算双方力量对比"""
        sides = self.get_sides()
        
        def calculate_strength(units: List[Dict]) -> float:
            strength = 0
            for unit in units:
                # 基础强度
                base = 1.0
                # 生命值影响
                health_factor = unit.get('sim_health', 100) / 100.0
                # 士气影响
                morale_factor = unit.get('sim_morale', 80) / 100.0
                # 单位类型加成
                type_factor = self._get_unit_type_factor(unit)
                
                strength += base * health_factor * morale_factor * type_factor
            
            return strength
        
        blue_strength = calculate_strength(sides['blue'])
        red_strength = calculate_strength(sides['red'])
        
        return {
            'blue': {
                'units': len(sides['blue']),
                'strength': blue_strength
            },
            'red': {
                'units': len(sides['red']),
                'strength': red_strength
            },
            'ratio': blue_strength / red_strength if red_strength > 0 else float('inf'),
            'advantage': 'blue' if blue_strength > red_strength else 'red'
        }
    
    def _get_unit_type_factor(self, unit: Dict) -> float:
        """获取单位类型加成系数"""
        unit_type = unit.get('type', '').lower()
        
        type_factors = {
            'infantry': 1.0,
            'tank': 2.5,
            'artillery': 2.0,
            'aircraft': 3.0,
            'navy': 3.5,
            'missile': 4.0,
            'radar': 0.5,
            'logistics': 0.3
        }
        
        for key, factor in type_factors.items():
            if key in unit_type:
                return factor
        
        return 1.0
    
    def export_state(self) -> Dict:
        """导出当前状态"""
        return {
            'total_units': len(self._units),
            'original_units': len(self._original_units),
            'temp_units': len(self._temp_units),
            'units': copy.deepcopy(list(self._units.values())),
            'force_ratio': self.calculate_force_ratio()
        }
    
    def clear(self):
        """清除所有数据"""
        self._units = {}
        self._original_units = {}
        self._temp_units = set()
        logger.info("单位管理器已清空")
    
    def __len__(self) -> int:
        """单位数量"""
        return len(self._units)
    
    def __contains__(self, unit_id: str) -> bool:
        """检查单位是否存在"""
        return str(unit_id) in self._units
    
    def __iter__(self):
        """迭代单位"""
        return iter(self._units.values())


def create_unit_manager(db_path: str = None) -> SimUnitManager:
    """创建单位管理器实例"""
    return SimUnitManager(db_path=db_path)


if __name__ == '__main__':
    manager = SimUnitManager()
    print(f"单位管理器初始化成功，当前单位数: {len(manager)}")
    manager.load_from_db()
    print(f"已加载单位数: {len(manager)}")