"""
天气影响计算器 - Weather Effect Calculator
计算天气对军事行动的影响
"""

import sys
import os
import copy
import logging
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)


class WeatherEffectCalculator:
    """
    天气影响计算器
    
    功能：
    - 获取指定位置的天气影响因子
    - 对单位应用天气效果
    - 检查天气是否适合特定操作
    """
    
    def __init__(self):
        """初始化天气影响计算器"""
        self._weather_service = None
        self._init_weather_service()
        
        # 天气效果系数表
        self.weather_effects = {
            'clear': {
                'visibility': 1.0,
                'mobility': 1.0,
                'comms': 1.0,
                'air_ops': 1.0,
                'ground_ops': 1.0,
                'naval_ops': 1.0
            },
            'cloudy': {
                'visibility': 0.9,
                'mobility': 0.95,
                'comms': 0.98,
                'air_ops': 0.85,
                'ground_ops': 0.98,
                'naval_ops': 0.95
            },
            'rain': {
                'visibility': 0.6,
                'mobility': 0.7,
                'comms': 0.8,
                'air_ops': 0.5,
                'ground_ops': 0.75,
                'naval_ops': 0.8
            },
            'storm': {
                'visibility': 0.3,
                'mobility': 0.4,
                'comms': 0.5,
                'air_ops': 0.2,
                'ground_ops': 0.5,
                'naval_ops': 0.4
            },
            'snow': {
                'visibility': 0.5,
                'mobility': 0.5,
                'comms': 0.85,
                'air_ops': 0.4,
                'ground_ops': 0.6,
                'naval_ops': 0.7
            },
            'fog': {
                'visibility': 0.25,
                'mobility': 0.8,
                'comms': 0.9,
                'air_ops': 0.3,
                'ground_ops': 0.85,
                'naval_ops': 0.6
            },
            'hot': {
                'visibility': 1.0,
                'mobility': 0.7,
                'comms': 1.0,
                'air_ops': 0.9,
                'ground_ops': 0.75,
                'naval_ops': 0.95
            },
            'cold': {
                'visibility': 0.9,
                'mobility': 0.6,
                'comms': 0.95,
                'air_ops': 0.85,
                'ground_ops': 0.65,
                'naval_ops': 0.8
            }
        }
    
    def _init_weather_service(self):
        """初始化天气服务"""
        try:
            from src.analysis.weather import WeatherService
            self._weather_service = WeatherService()
            logger.info("天气服务已连接")
        except ImportError:
            logger.warning("天气服务不可用，使用默认天气")
            self._weather_service = None
    
    def get_weather_factor(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        获取指定位置的天气影响因子
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            天气影响因子字典
        """
        # 尝试从天气服务获取
        weather_data = None
        if self._weather_service:
            try:
                weather_data = self._weather_service.get_weather_factor(lat, lng)
            except Exception as e:
                logger.warning(f"获取天气数据失败: {e}")
        
        # 如果没有数据，使用默认天气
        if not weather_data:
            weather_data = self._get_default_weather()
        
        return self._process_weather_data(weather_data, lat, lng)
    
    def _get_default_weather(self) -> Dict:
        """获取默认天气数据"""
        return {
            'condition': 'clear',
            'temperature': 20,
            'wind_speed': 10,
            'humidity': 50,
            'visibility': 10
        }
    
    def _process_weather_data(self, weather_data: Dict, lat: float, lng: float) -> Dict:
        """处理天气数据，生成影响因子"""
        condition = weather_data.get('condition', 'clear')
        
        # 获取基础效果
        base_effects = self.weather_effects.get(condition, self.weather_effects['clear'])
        
        # 计算综合修正
        temperature = weather_data.get('temperature', 20)
        wind_speed = weather_data.get('wind_speed', 10)
        visibility = weather_data.get('visibility', 10)
        
        # 温度影响
        temp_factor = 1.0
        if temperature > 35:
            temp_factor = 0.85
        elif temperature < -10:
            temp_factor = 0.75
        
        # 风速影响
        wind_factor = 1.0
        if wind_speed > 50:
            wind_factor = 0.7
        elif wind_speed > 30:
            wind_factor = 0.85
        
        # 能见度影响
        vis_factor = min(1.0, visibility / 10.0)
        
        # 综合计算
        effects = copy.deepcopy(base_effects)
        for key in effects:
            effects[key] *= temp_factor * wind_factor * vis_factor
        
        # 返回完整数据
        return {
            'condition': condition,
            'temperature': temperature,
            'wind_speed': wind_speed,
            'humidity': weather_data.get('humidity', 50),
            'visibility': visibility,
            'effects': effects,
            'combat_modifier': (effects['air_ops'] + effects['ground_ops']) / 2,
            'location': {'lat': lat, 'lng': lng},
            'timestamp': weather_data.get('timestamp', '')
        }
    
    def apply_weather_to_units(self, units: Dict[str, Dict], weather: Dict) -> Dict[str, Dict]:
        """
        对单位应用天气效果
        
        Args:
            units: 单位字典
            weather: 天气数据
            
        Returns:
            更新后的单位字典
        """
        if not weather:
            return units
        
        effects = weather.get('effects', {})
        if not effects:
            return units
        
        updated_units = copy.deepcopy(units)
        
        for unit_id, unit in updated_units.items():
            unit_type = unit.get('type', '').lower()
            
            # 根据单位类型应用不同效果
            if any(t in unit_type for t in ['aircraft', 'plane', 'air']):
                # 空中单位主要受制于空中作战条件
                morale_factor = effects.get('air_ops', 1.0)
            elif any(t in unit_type for t in ['navy', 'ship', 'submarine', 'naval']):
                # 海军单位受制于海上条件
                morale_factor = effects.get('naval_ops', 1.0)
            else:
                # 地面单位受制于地面条件
                morale_factor = effects.get('ground_ops', 1.0)
            
            # 更新单位士气（天气影响士气）
            current_morale = unit.get('sim_morale', 80)
            new_morale = current_morale * morale_factor
            unit['sim_morale'] = new_morale
            
            # 额外：限制移动（如果移动性差）
            if effects.get('mobility', 1.0) < 0.7:
                unit['movement_penalty'] = True
        
        return updated_units
    
    def get_suitable_conditions(self, units: List[Dict], operation_type: str = 'ground') -> Dict:
        """
        检查天气是否适合特定操作
        
        Args:
            units: 单位列表
            operation_type: 操作类型 (ground/air/naval)
            
        Returns:
            适合作战条件评估
        """
        # 获取第一个单位位置的天气（假设同一区域）
        if not units:
            return {'suitable': True, 'conditions': 'no_units'}
        
        first_unit = units[0]
        lat = first_unit.get('latitude') or first_unit.get('sim_position', {}).get('lat', 0)
        lng = first_unit.get('longitude') or first_unit.get('sim_position', {}).get('lng', 0)
        
        weather = self.get_weather_factor(lat, lng)
        effects = weather.get('effects', {})
        
        # 获取对应操作类型的效果
        op_key = f"{operation_type}_ops"
        op_factor = effects.get(op_key, 1.0)
        
        return {
            'suitable': op_factor >= 0.5,
            'factor': op_factor,
            'condition': weather.get('condition', 'unknown'),
            'visibility': weather.get('visibility', 0),
            'recommendation': self._get_recommendation(op_factor)
        }
    
    def _get_recommendation(self, factor: float) -> str:
        """根据因素获取建议"""
        if factor >= 0.9:
            return "非常适合作战"
        elif factor >= 0.7:
            return "适合作战"
        elif factor >= 0.5:
            return "勉强适合，建议谨慎"
        elif factor >= 0.3:
            return "不适合进攻，建议防御"
        else:
            return "不适合任何军事行动"
    
    def get_weather_forecast(self, lat: float, lng: float, hours: int = 24) -> List[Dict]:
        """获取天气预报"""
        forecast = []
        
        # 获取当前天气
        current = self.get_weather_factor(lat, lng)
        forecast.append(current)
        
        # 模拟未来天气变化（简化模型）
        conditions = ['clear', 'cloudy', 'rain', 'storm', 'fog']
        
        for i in range(1, hours // 6 + 1):
            weather = copy.deepcopy(current)
            # 随机变化天气状态
            import random
            idx = random.randint(0, len(conditions) - 1)
            weather['condition'] = conditions[idx]
            weather['visibility'] = random.randint(3, 15)
            weather['wind_speed'] = random.randint(5, 40)
            weather['timestamp'] = f"+{i*6}h"
            
            forecast.append(weather)
        
        return forecast
    
    def calculate_weather_impact(self, units: List[Dict], weather: Dict) -> Dict:
        """计算天气对单位的整体影响"""
        if not units or not weather:
            return {
                'total_units': 0,
                'affected_units': 0,
                'avg_morale_impact': 1.0,
                'movement_limited': False
            }
        
        effects = weather.get('effects', {})
        total_units = len(units)
        affected_units = 0
        total_morale_impact = 0
        
        for unit in units:
            unit_type = unit.get('type', '').lower()
            
            if any(t in unit_type for t in ['aircraft', 'plane', 'air']):
                factor = effects.get('air_ops', 1.0)
            elif any(t in unit_type for t in ['navy', 'ship', 'naval']):
                factor = effects.get('naval_ops', 1.0)
            else:
                factor = effects.get('ground_ops', 1.0)
            
            total_morale_impact += factor
            if factor < 0.8:
                affected_units += 1
        
        avg_impact = total_morale_impact / total_units if total_units > 0 else 1.0
        
        return {
            'total_units': total_units,
            'affected_units': affected_units,
            'avg_morale_impact': avg_impact,
            'movement_limited': effects.get('mobility', 1.0) < 0.7,
            'air_ops_impact': effects.get('air_ops', 1.0),
            'ground_ops_impact': effects.get('ground_ops', 1.0),
            'naval_ops_impact': effects.get('naval_ops', 1.0)
        }


def create_weather_calculator() -> WeatherEffectCalculator:
    """创建天气影响计算器实例"""
    return WeatherEffectCalculator()


if __name__ == '__main__':
    calculator = WeatherEffectCalculator()
    
    # 测试
    weather = calculator.get_weather_factor(39.9, 116.4)  # 北京
    print(f"天气条件: {weather.get('condition')}")
    print(f"作战修正: {weather.get('combat_modifier'):.2f}")
    print(f"效果: {weather.get('effects')}")