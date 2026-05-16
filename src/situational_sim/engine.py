"""
模拟情境引擎 - Simulation Situation Engine
核心引擎：数据隔离保护，启动时复制DB数据，结束时不修改原始数据
"""

import sys
import os
import json
import copy
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)


class SimSituationEngine:
    """
    情境模拟引擎 - 提供完整的战场模拟功能
    
    核心原则：
    - 启动模拟时：从原始数据库复制所有单位数据
    - 模拟过程中：只修改模拟数据副本
    - 结束模拟时：丢弃所有模拟数据，恢复原始状态
    - 原始数据：完全不变
    """
    
    def __init__(self, db_path: str = None):
        """初始化模拟引擎
        
        Args:
            db_path: 数据库路径，默认使用项目配置
        """
        self.db_path = db_path or self._get_default_db_path()
        self.sim_units = {}
        self.sim_state = {
            'is_running': False,
            'current_step': 0,
            'start_time': None,
            'events': [],
            'original_snapshot': None
        }
        self._unit_manager = None
        self._battle_sim = None
        self._weather_effect = None
        self._report = None
        
        self._init_modules()
        
    def _get_default_db_path(self) -> str:
        """获取默认数据库路径"""
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        return os.path.join(project_root, 'data', 'military_monitor.db')
    
    def _init_modules(self):
        """初始化依赖模块"""
        try:
            from src.situational_sim.unit_manager import SimUnitManager
            from src.situational_sim.battle_sim import BattleSimulator
            from src.situational_sim.weather_effect import WeatherEffectCalculator
            from src.situational_sim.report import SimulationReport
            
            self._unit_manager = SimUnitManager()
            self._battle_sim = BattleSimulator()
            self._weather_effect = WeatherEffectCalculator()
            self._report = SimulationReport()
        except ImportError as e:
            logger.warning(f"模块导入警告: {e}")
    
    def start_simulation(self) -> Dict[str, Any]:
        """启动模拟 - 关键操作：复制DB数据到模拟存储"""
        if self.sim_state['is_running']:
            logger.warning("模拟已在运行中，请先结束当前模拟")
            return {'status': 'running', 'message': '模拟已在运行'}
        
        logger.info("启动模拟引擎：从数据库复制原始数据...")
        
        try:
            self._save_original_snapshot()
            cloned_units = self._clone_all_units_from_db()
            
            self.sim_units = cloned_units
            self.sim_state['is_running'] = True
            self.sim_state['current_step'] = 0
            self.sim_state['start_time'] = datetime.now().isoformat()
            self.sim_state['events'] = []
            
            if self._unit_manager:
                self._unit_manager.reset_to_original()
                for unit_id, unit_data in cloned_units.items():
                    self._unit_manager.add_unit(unit_data)
            
            result = {
                'status': 'success',
                'message': '模拟启动成功，原始数据已复制',
                'units_loaded': len(cloned_units),
                'sim_start_time': self.sim_state['start_time']
            }
            
            logger.info(f"模拟启动成功：已加载 {len(cloned_units)} 个单位")
            return result
            
        except Exception as e:
            logger.error(f"模拟启动失败: {e}")
            self._cleanup_on_error()
            return {'status': 'error', 'message': str(e)}
    
    def _save_original_snapshot(self):
        """保存原始数据快照"""
        try:
            original_units = self._fetch_units_from_db()
            self.sim_state['original_snapshot'] = copy.deepcopy(original_units)
            logger.info(f"原始数据快照已保存: {len(original_units)} 个单位")
        except Exception as e:
            logger.error(f"保存原始快照失败: {e}")
            self.sim_state['original_snapshot'] = {}
    
    def _fetch_units_from_db(self) -> Dict[str, Dict]:
        """从数据库获取所有单位数据"""
        units = {}
        
        try:
            import sqlite3
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                table_names = ['units', 'military_units', 'unit_positions']
                
                for table in table_names:
                    try:
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
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
            logger.warning(f"数据库读取失败，使用空数据: {e}")
        
        return units
    
    def _clone_all_units_from_db(self) -> Dict[str, Dict]:
        """克隆所有单位数据 - 核心数据隔离操作"""
        original_units = self._fetch_units_from_db()
        cloned_units = {}
        
        for unit_id, unit_data in original_units.items():
            cloned_unit = copy.deepcopy(unit_data)
            
            cloned_unit['sim_id'] = f"sim_{unit_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cloned_unit['sim_health'] = cloned_unit.get('health', 100)
            cloned_unit['sim_morale'] = cloned_unit.get('morale', 80)
            cloned_unit['sim_position'] = {
                'lat': cloned_unit.get('latitude') or cloned_unit.get('lat', 0),
                'lng': cloned_unit.get('longitude') or cloned_unit.get('lng', 0)
            }
            cloned_unit['sim_status'] = 'active'
            cloned_unit['is_temp_unit'] = False
            
            cloned_units[str(unit_id)] = cloned_unit
        
        logger.info(f"已克隆 {len(cloned_units)} 个单位到模拟存储")
        return cloned_units
    
    def clone_unit(self, unit_id: str) -> Optional[Dict]:
        """克隆指定单位用于模拟"""
        if not self.sim_state['is_running']:
            logger.warning("模拟未运行，请先启动模拟")
            return None
        
        original_unit = self.sim_units.get(str(unit_id))
        if original_unit:
            return copy.deepcopy(original_unit)
        return None
    
    def add_sim_unit(self, unit_data: Dict) -> str:
        """添加临时模拟单位 - 不存在于原始数据库"""
        if not self.sim_state['is_running']:
            logger.warning("模拟未运行，请先启动模拟")
            return None
        
        temp_id = f"temp_{len(self.sim_units)}_{datetime.now().strftime('%H%M%S')}"
        
        sim_unit = copy.deepcopy(unit_data)
        sim_unit['sim_id'] = temp_id
        sim_unit['is_temp_unit'] = True
        sim_unit['sim_health'] = sim_unit.get('health', 100)
        sim_unit['sim_morale'] = sim_unit.get('morale', 80)
        sim_unit['sim_status'] = 'active'
        
        if 'sim_position' not in sim_unit:
            sim_unit['sim_position'] = {
                'lat': unit_data.get('latitude') or unit_data.get('lat', 0),
                'lng': unit_data.get('longitude') or unit_data.get('lng', 0)
            }
        
        self.sim_units[temp_id] = sim_unit
        
        logger.info(f"添加临时单位: {temp_id}")
        return temp_id
    
    def update_unit_param(self, unit_id: str, param: str, value: Any) -> bool:
        """更新模拟单位参数 - 仅修改模拟副本"""
        if not self.sim_state['is_running']:
            logger.warning("模拟未运行，请先启动模拟")
            return False
        
        unit_id_str = str(unit_id)
        if unit_id_str not in self.sim_units:
            logger.warning(f"单位 {unit_id} 不在模拟存储中")
            return False
        
        self.sim_units[unit_id_str][param] = value
        
        if param in ['health', 'morale', 'position', 'status']:
            sim_param = f"sim_{param}"
            self.sim_units[unit_id_str][sim_param] = value
            
            if param == 'position':
                self.sim_units[unit_id_str]['sim_position'] = value
        
        logger.debug(f"更新单位 {unit_id} 参数 {param} = {value}")
        return True
    
    def update_unit(self, unit_id: str, param: str, value: Any) -> bool:
        """更新单位的简写方法"""
        return self.update_unit_param(unit_id, param, value)
    
    def run_simulation(self, steps: int = 1, weather_data: Dict = None) -> Dict[str, Any]:
        """运行模拟步骤"""
        if not self.sim_state['is_running']:
            logger.warning("模拟未运行，请先启动模拟")
            return {'status': 'error', 'message': '模拟未运行'}
        
        logger.info(f"开始模拟: {steps} 步")
        
        results = {
            'status': 'success',
            'steps_completed': 0,
            'events': [],
            'casualties': {},
            'territory_change': {}
        }
        
        for step in range(steps):
            self.sim_state['current_step'] += 1
            
            weather_factor = {}
            if weather_data:
                weather_factor = weather_data
            elif self._weather_effect:
                weather_factor = self._get_current_weather()
            
            if self._weather_effect and weather_factor:
                self.sim_units = self._weather_effect.apply_weather_to_units(
                    self.sim_units, weather_factor
                )
            
            step_result = self._execute_battle_step(weather_factor)
            
            results['events'].extend(step_result.get('events', []))
            results['casualties'].update(step_result.get('casualties', {}))
            results['steps_completed'] += 1
            
            self._record_event({
                'step': self.sim_state['current_step'],
                'type': 'simulation_step',
                'details': step_result
            })
        
        logger.info(f"模拟完成: {steps} 步")
        return results
    
    def _get_current_weather(self) -> Dict:
        """获取当前天气数据"""
        try:
            from src.analysis.weather import WeatherService
            weather_service = WeatherService()
            return weather_service.get_weather_factor(0, 0) or {}
        except:
            return {}
    
    def _execute_battle_step(self, weather: Dict) -> Dict:
        """执行单步战斗模拟"""
        if not self._battle_sim:
            return {'events': [], 'casualties': {}}
        
        return self._battle_sim.simulate_step(self.sim_units, weather)
    
    def get_sim_state(self) -> Dict[str, Any]:
        """获取当前模拟状态快照"""
        return {
            'is_running': self.sim_state['is_running'],
            'current_step': self.sim_state['current_step'],
            'start_time': self.sim_state['start_time'],
            'units_count': len(self.sim_units),
            'temp_units_count': sum(1 for u in self.sim_units.values() if u.get('is_temp_unit', False)),
            'events_count': len(self.sim_state['events']),
            'units': copy.deepcopy(self.sim_units)
        }
    
    def reset_unit(self, unit_id: str) -> bool:
        """重置单个单位到原始状态"""
        if not self.sim_state['is_running']:
            return False
        
        original_units = self.sim_state.get('original_snapshot', {})
        unit_id_str = str(unit_id)
        
        if self.sim_units.get(unit_id_str, {}).get('is_temp_unit', False):
            del self.sim_units[unit_id_str]
            logger.info(f"移除临时单位: {unit_id}")
            return True
        
        if unit_id_str in original_units:
            self.sim_units[unit_id_str] = copy.deepcopy(original_units[unit_id_str])
            logger.info(f"重置单位 {unit_id} 到原始状态")
            return True
        
        return False
    
    def clear_simulation(self):
        """清除所有模拟数据"""
        if self.sim_state['is_running']:
            logger.warning("请先使用 end_simulation() 正确结束模拟")
            return
        
        self.sim_units = {}
        self.sim_state = {
            'is_running': False,
            'current_step': 0,
            'start_time': None,
            'events': [],
            'original_snapshot': None
        }
        logger.info("模拟数据已清除")
    
    def end_simulation(self, save_report: bool = False) -> Dict[str, Any]:
        """结束模拟 - 关键操作：丢弃模拟数据，恢复原始状态"""
        if not self.sim_state['is_running']:
            logger.warning("模拟未运行")
            return {'status': 'idle', 'message': '模拟未运行'}
        
        logger.info("结束模拟：丢弃模拟数据，恢复原始状态...")
        
        try:
            report = None
            if save_report:
                report = self.generate_final_report()
            
            self._discard_sim_data()
            
            self.sim_state['is_running'] = False
            self.sim_state['current_step'] = 0
            
            result = {
                'status': 'success',
                'message': '模拟已结束，所有模拟数据已丢弃，原始数据未受影响',
                'report': report
            }
            
            logger.info("模拟结束成功")
            return result
            
        except Exception as e:
            logger.error(f"结束模拟失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _discard_sim_data(self):
        """丢弃所有模拟数据"""
        self.sim_units = {}
        self.sim_state['events'] = []
        self.sim_state['original_snapshot'] = None
        logger.info("模拟数据已完全丢弃")
    
    def _cleanup_on_error(self):
        """错误时清理"""
        self._discard_sim_data()
        self.sim_state['is_running'] = False
    
    def export_sim_result(self, format: str = 'json') -> str:
        """导出模拟结果"""
        if not self.sim_state['is_running']:
            return json.dumps({
                'status': 'error',
                'message': '模拟未运行'
            }, ensure_ascii=False)
        
        report = self.generate_final_report()
        
        if format == 'text':
            return self._format_report_as_text(report)
        
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    def generate_final_report(self) -> Dict:
        """生成最终模拟报告"""
        if self._report:
            return self._report.generate(
                self.sim_state.get('original_snapshot', {}),
                self.sim_units,
                self.sim_state.get('events', [])
            )
        
        return {
            'sim_status': 'completed',
            'steps': self.sim_state['current_step'],
            'total_units': len(self.sim_units),
            'events_count': len(self.sim_state['events']),
            'timestamp': datetime.now().isoformat()
        }
    
    def _format_report_as_text(self, report: Dict) -> str:
        """格式化报告为文本"""
        lines = []
        lines.append("=" * 60)
        lines.append("模拟情境报告 - Simulation Report")
        lines.append("=" * 60)
        lines.append(f"模拟状态: {report.get('sim_status', 'unknown')}")
        lines.append(f"模拟步数: {report.get('steps', 0)}")
        lines.append(f"单位总数: {report.get('total_units', 0)}")
        lines.append(f"事件数量: {report.get('events_count', 0)}")
        lines.append(f"生成时间: {report.get('timestamp', 'N/A')}")
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def export_map_snapshot(self, config: Dict = None) -> Dict:
        """导出地图快照元数据"""
        if not config:
            config = {}
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'step': self.sim_state['current_step'],
            'units': [],
            'bounds': {'min_lat': 90, 'max_lat': -90, 'min_lng': 180, 'max_lng': -180}
        }
        
        for unit_id, unit in self.sim_units.items():
            pos = unit.get('sim_position', {})
            lat = pos.get('lat', 0)
            lng = pos.get('lng', 0)
            
            snapshot['units'].append({
                'id': unit_id,
                'type': unit.get('type', 'unknown'),
                'side': unit.get('side', unit.get('force', 'unknown')),
                'position': {'lat': lat, 'lng': lng},
                'health': unit.get('sim_health', 100),
                'status': unit.get('sim_status', 'active')
            })
            
            snapshot['bounds']['min_lat'] = min(snapshot['bounds']['min_lat'], lat)
            snapshot['bounds']['max_lat'] = max(snapshot['bounds']['max_lat'], lat)
            snapshot['bounds']['min_lng'] = min(snapshot['bounds']['min_lng'], lng)
            snapshot['bounds']['max_lng'] = max(snapshot['bounds']['max_lng'], lng)
        
        return snapshot
    
    def get_units(self) -> List[Dict]:
        """获取所有模拟单位"""
        return list(self.sim_units.values())
    
    def get_unit(self, unit_id: str) -> Optional[Dict]:
        """获取指定单位"""
        return self.sim_units.get(str(unit_id))
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_simulation()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type:
            logger.error(f"模拟异常: {exc_val}")
            self._cleanup_on_error()
        else:
            self.end_simulation()
        return False
    
    def _record_event(self, event: Dict):
        """记录模拟事件"""
        self.sim_state['events'].append({
            'timestamp': datetime.now().isoformat(),
            **event
        })


def create_sim_engine(db_path: str = None) -> 'SimSituationEngine':
    """创建模拟引擎实例"""
    return SimSituationEngine(db_path=db_path)


if __name__ == '__main__':
    engine = SimSituationEngine()
    print("模拟引擎初始化成功")
    print(f"当前状态: {engine.get_sim_state()}")