# -*- coding: utf-8 -*-
"""
地形与气象分析模块
提供地形评分、天气影响、综合性分析建议
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import math
import random
from typing import Dict, Any, List, Optional

from src.analysis.weather import WeatherService


class TerrainAnalysis:
    """
    地形分析器
    基于地理位置进行地形特征评分
    评估防御优势、机动难度、适宜性
    """
    
    def __init__(self):
        self.weather_service = WeatherService()
    
    def analyze(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        分析指定坐标的地形特征
        
        使用简化的地形评分模型：
        - 考虑纬度（高纬度地形通常更崎岖）
        - 考虑经度（不同区域地形特征）
        - 生成模拟地形类型
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            包含地形评分和分析结果的字典
        """
        # 基础地形评分（模拟，实际应用中需要GIS数据）
        terrain_score = self._calculate_terrain_score(lat, lng)
        
        # 地形类型分类
        terrain_type = self._classify_terrain(terrain_score)
        
        # 防御加成（崎岖地形防御优势更大）
        if terrain_score >= 70:
            defense_bonus = 30.0
            defense_desc = "地形险要，易守难攻"
        elif terrain_score >= 50:
            defense_bonus = 15.0
            defense_desc = "有一定地形优势"
        elif terrain_score >= 30:
            defense_bonus = 0.0
            defense_desc = "普通地形"
        else:
            defense_bonus = -10.0
            defense_desc = "地势开阔，防御劣势"
        
        # 机动难度
        mobility_factor = self._calculate_mobility_factor(terrain_score)
        
        # 适用性评估
        suitability = self._assess_suitability(terrain_score, lat)
        
        return {
            'latitude': lat,
            'longitude': lng,
            'terrain_score': terrain_score,
            'terrain_type': terrain_type,
            'defense_bonus': defense_bonus,
            'defense_description': defense_desc,
            'mobility_factor': mobility_factor,
            'suitability': suitability,
            'movement_difficulty': 'high' if mobility_factor > 1.5 else 'medium' if mobility_factor > 1.0 else 'low',
            'cover_options': self._estimate_cover_options(terrain_score),
            'observation_quality': self._estimate_observation(terrain_score, lat)
        }
    
    def _calculate_terrain_score(self, lat: float, lng: float) -> float:
        """
        计算地形评分（0-100）
        
        综合考虑：
        - 基础地形复杂度（基于坐标模拟）
        - 高度变化（模拟）
        - 植被覆盖（模拟）
        """
        # 基础评分（基于经纬度的伪随机模拟）
        base = math.sin(lat * 0.1) * math.cos(lng * 0.05) * 50 + 50
        
        # 添加一些模拟变化
        variation = (hash(f"{lat:.2f},{lng:.2f}") % 100) / 100.0 * 30
        
        score = base + variation
        
        # 确保在0-100范围内
        return max(0.0, min(100.0, score))
    
    def _classify_terrain(self, score: float) -> str:
        """根据评分分类地形类型"""
        if score >= 80:
            return "mountain"  # 山区
        elif score >= 60:
            return "hills"  # 丘陵
        elif score >= 40:
            return "plains"  # 平原
        elif score >= 20:
            return "desert"  # 沙漠/荒原
        else:
            return "water"  # 水域/湿地
    
    def _calculate_mobility_factor(self, terrain_score: float) -> float:
        """
        计算机动性系数
        
        地形越复杂，机动性越差，系数越高
        """
        # 将地形评分转换为机动系数（0.5-3.0）
        mobility = 3.0 - (terrain_score / 100.0 * 2.5)
        return max(0.5, min(3.0, mobility))
    
    def _assess_suitability(self, terrain_score: float, lat: float) -> Dict[str, Any]:
        """评估不同军事行动的适宜性"""
        suitability = {
            'offensive': {'score': 0, 'desc': ''},
            'defensive': {'score': 0, 'desc': ''},
            'reconnaissance': {'score': 0, 'desc': ''},
            'air_operation': {'score': 0, 'desc': ''}
        }
        
        # 进攻适宜性（中等复杂地形最适宜）
        if 40 <= terrain_score <= 60:
            suitability['offensive']['score'] = 80
            suitability['offensive']['desc'] = "地形适度复杂，有利于突击"
        elif terrain_score < 40:
            suitability['offensive']['score'] = 90
            suitability['offensive']['desc'] = "开阔地形，机动快速"
        else:
            suitability['offensive']['score'] = 40
            suitability['offensive']['desc'] = "地形复杂，进攻困难"
        
        # 防御适宜性（复杂地形更适宜）
        if terrain_score >= 70:
            suitability['defensive']['score'] = 95
            suitability['defensive']['desc'] = "天然屏障，防御优势明显"
        elif terrain_score >= 50:
            suitability['defensive']['score'] = 70
            suitability['defensive']['desc'] = "有一定防御优势"
        else:
            suitability['defensive']['score'] = 40
            suitability['defensive']['desc'] = "开阔地形，防御困难"
        
        # 侦察适宜性
        if 30 <= terrain_score <= 50:
            suitability['reconnaissance']['score'] = 85
            suitability['reconnaissance']['desc'] = "视野开阔，便于观察"
        elif terrain_score < 30:
            suitability['reconnaissance']['score'] = 70
            suitability['reconnaissance']['desc'] = "视野良好"
        else:
            suitability['reconnaissance']['score'] = 50
            suitability['reconnaissance']['desc'] = "遮蔽物多，但视野受限"
        
        # 空中作战适宜性（与纬度相关）
        if abs(lat) > 60:
            suitability['air_operation']['score'] = 50
            suitability['air_operation']['desc'] = "高纬度，气象条件复杂"
        elif terrain_score > 70:
            suitability['air_operation']['score'] = 60
            suitability['air_operation']['desc'] = "地形复杂，规避空间大"
        else:
            suitability['air_operation']['score'] = 85
            suitability['air_operation']['desc'] = "低空飞行条件良好"
        
        return suitability
    
    def _estimate_cover_options(self, terrain_score: float) -> Dict[str, int]:
        """估算掩护选项数量（1-10）"""
        if terrain_score >= 80:
            return {'natural': 9, 'artificial': 3, 'total': 12}
        elif terrain_score >= 60:
            return {'natural': 7, 'artificial': 5, 'total': 12}
        elif terrain_score >= 40:
            return {'natural': 4, 'artificial': 6, 'total': 10}
        else:
            return {'natural': 1, 'artificial': 8, 'total': 9}
    
    def _estimate_observation(self, terrain_score: float, lat: float) -> Dict[str, Any]:
        """估算观察条件"""
        if terrain_score >= 70:
            visibility_range = "limited"  # 有限
            advantage = "对己方有利（隐蔽性好）"
        elif terrain_score >= 40:
            visibility_range = "moderate"  # 中等
            advantage = "均衡"
        else:
            visibility_range = "extended"  # 开阔
            advantage = "对方有利（视野开阔）"
        
        # 高纬度地区能见度变化大
        if abs(lat) > 50:
            weather_factor = "受极地气候影响大"
        else:
            weather_factor = "受季风/降水影响"
        
        return {
            'visibility_range': visibility_range,
            'weather_factor': weather_factor,
            'advantage': advantage
        }
    
    def get_weather_impact(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        获取指定坐标的天气影响分析
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            天气影响分析结果
        """
        try:
            # 调用WeatherService获取天气数据
            weather_data = self.weather_service.get_current_weather(lat, lng)
            
            return self._analyze_weather_impact(weather_data)
            
        except Exception as e:
            print(f"获取天气数据失败: {e}")
            # 返回默认分析
            return {
                'weather_status': 'unknown',
                'temperature': 'N/A',
                'visibility': 'N/A',
                'wind_speed': 'N/A',
                'precipitation': 'N/A',
                'impact_on_operations': {
                    'air': '无法评估',
                    'ground': '无法评估',
                    'naval': '无法评估'
                },
                'overall_impact': '气象数据不可用'
            }
    
    def _analyze_weather_impact(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析天气对军事行动的影响"""
        # 解析天气数据
        weather_status = weather_data.get('weather', 'clear')
        temp = weather_data.get('temperature', 20)
        visibility = weather_data.get('visibility', 10)  # 公里
        wind = weather_data.get('wind_speed', 0)  # m/s
        
        # 空中作战影响评估
        if visibility < 2 or wind > 15:
            air_impact = "严重受限"
            air_score = 20
        elif visibility < 5 or wind > 10:
            air_impact = "明显受限"
            air_score = 50
        elif visibility < 10 or wind > 5:
            air_impact = "轻度受限"
            air_score = 75
        else:
            air_impact = "适宜飞行"
            air_score = 95
        
        # 地面作战影响评估
        if 'rain' in weather_status.lower() or 'snow' in weather_status.lower():
            ground_impact = "行动受限"
            ground_score = 60
        elif visibility < 5:
            ground_impact = "观察受限"
            ground_score = 70
        else:
            ground_impact = "适宜行动"
            ground_score = 90
        
        # 海军作战影响评估
        if wind > 15 or 'storm' in weather_status.lower():
            naval_impact = "不可作业"
            naval_score = 10
        elif wind > 10:
            naval_impact = "行动受限"
            naval_score = 50
        else:
            naval_impact = "正常作业"
            naval_score = 80
        
        # 综合影响评分
        overall_score = (air_score + ground_score + naval_score) / 3
        
        if overall_score >= 80:
            overall_impact = "气象条件优良"
        elif overall_score >= 60:
            overall_impact = "气象条件一般"
        elif overall_score >= 40:
            overall_impact = "气象条件较差"
        else:
            overall_impact = "气象条件恶劣"
        
        return {
            'weather_status': weather_status,
            'temperature': f"{temp}°C" if isinstance(temp, (int, float)) else temp,
            'visibility': f"{visibility}km" if isinstance(visibility, (int, float)) else visibility,
            'wind_speed': f"{wind}m/s" if isinstance(wind, (int, float)) else wind,
            'impact_on_operations': {
                'air': air_impact,
                'air_score': air_score,
                'ground': ground_impact,
                'ground_score': ground_score,
                'naval': naval_impact,
                'naval_score': naval_score
            },
            'overall_impact': overall_impact,
            'recommendations': self._generate_weather_recommendations(
                weather_status, visibility, wind
            )
        }
    
    def _generate_weather_recommendations(
        self, 
        weather: str, 
        visibility: float, 
        wind: float
    ) -> List[str]:
        """生成天气相关建议"""
        recommendations = []
        
        if visibility < 2:
            recommendations.append("能见度极低，建议暂停空中行动")
        elif visibility < 5:
            recommendations.append("能见度较低，飞行需谨慎")
        
        if wind > 15:
            recommendations.append("大风天气，不宜无人机作业")
        elif wind > 10:
            recommendations.append("注意风力对飞行器的影响")
        
        if 'rain' in weather.lower():
            recommendations.append("降雨天气，地面装备注意防滑")
        elif 'snow' in weather.lower():
            recommendations.append("降雪天气，注意装备保暖和机动性")
        elif 'fog' in weather.lower():
            recommendations.append("大雾天气，可见距离严重受限")
        
        if not recommendations:
            recommendations.append("当前天气条件良好，适合各类军事行动")
        
        return recommendations
    
    def combined_analysis(
        self, 
        lat: float, 
        lng: float, 
        units: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        综合地形和天气分析
        
        Args:
            lat: 纬度
            lng: 经度
            units: 附近的单位列表（可选）
            
        Returns:
            综合分析结果
        """
        # 地形分析
        terrain = self.analyze(lat, lng)
        
        # 天气影响分析
        weather = self.get_weather_impact(lat, lng)
        
        # 生成综合建议
        recommendation = self._generate_comprehensive_recommendation(
            terrain, weather, units
        )
        
        return {
            'latitude': lat,
            'longitude': lng,
            'terrain_analysis': {
                'score': terrain['terrain_score'],
                'type': terrain['terrain_type'],
                'defense_bonus': terrain['defense_bonus'],
                'mobility_factor': terrain['mobility_factor'],
                'movement_difficulty': terrain['movement_difficulty'],
                'suitability': terrain['suitability']
            },
            'weather_impact': weather.get('overall_impact', '未知'),
            'visibility': weather.get('visibility', 'N/A'),
            'operations_assessment': weather.get('impact_on_operations', {}),
            'recommendation': recommendation,
            'threat_level': self._assess_threat_level(terrain, weather, units),
            'timestamp': self._get_timestamp()
        }
    
    def _generate_comprehensive_recommendation(
        self, 
        terrain: Dict[str, Any], 
        weather: Dict[str, Any], 
        units: List[Dict[str, Any]] = None
    ) -> str:
        """生成综合建议"""
        recommendations = []
        
        # 地形建议
        terrain_score = terrain['terrain_score']
        mobility = terrain['mobility_factor']
        
        if terrain_score >= 70:
            recommendations.append("地形险要，适合防御部署，建议利用地形优势设置阵地")
            if mobility > 1.5:
                recommendations.append("复杂地形限制大规模机动，建议小规模分散行动")
        elif terrain_score <= 30:
            recommendations.append("开阔地形适合快速机动，但需注意暴露风险")
        
        # 天气建议
        operations = weather.get('impact_on_operations', {})
        
        air_impact = operations.get('air', 'unknown')
        if '受限' in air_impact or '不可' in air_impact:
            recommendations.append(f"空中行动{air_impact}，建议启用备用方案或调整行动时间")
        
        ground_impact = operations.get('ground', 'unknown')
        if '受限' in ground_impact:
            recommendations.append("地面行动受天气影响，建议加强防护措施")
        
        # 单位存在时的建议
        if units:
            unit_count = len(units)
            recommendations.append(f"附近检测到约{unit_count}个单位，建议加强警戒级别")
            
            # 分析单位类型
            aircraft = [u for u in units if 'air' in u.get('unit_type', '').lower()]
            if aircraft:
                recommendations.append(f"其中{len(aircraft)}个空中目标，注意防空警戒")
        
        # 综合优先级建议
        if not recommendations:
            recommendations.append("当前态势良好，建议保持常规巡逻和监控")
        
        return "; ".join(recommendations)
    
    def _assess_threat_level(
        self, 
        terrain: Dict[str, Any], 
        weather: Dict[str, Any],
        units: List[Dict[str, Any]] = None
    ) -> str:
        """评估威胁等级"""
        score = 50  # 基础分
        
        # 地形因素
        if terrain['terrain_score'] < 30:  # 开阔地形
            score += 15
        
        # 天气因素
        operations = weather.get('impact_on_operations', {})
        air_score = operations.get('air_score', 80)
        if air_score < 50:
            score += 20
        
        # 单位因素
        if units:
            score += min(30, len(units) * 3)
        
        # 威胁等级判定
        if score >= 80:
            return "极高"
        elif score >= 60:
            return "高"
        elif score >= 40:
            return "中"
        else:
            return "低"
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    # 测试代码
    analyzer = TerrainAnalysis()
    
    # 测试坐标
    test_lat, test_lng = 39.9042, 116.4074  # 北京
    
    print(f"地形与气象分析测试 - 坐标: ({test_lat}, {test_lng})")
    print("=" * 50)
    
    # 地形分析
    terrain = analyzer.analyze(test_lat, test_lng)
    print(f"\n【地形分析】")
    print(f"  评分: {terrain['terrain_score']:.1f}/100")
    print(f"  类型: {terrain['terrain_type']}")
    print(f"  防御加成: {terrain['defense_bonus']:.1f}%")
    print(f"  机动系数: {terrain['mobility_factor']:.2f}")
    
    # 天气影响
    weather = analyzer.get_weather_impact(test_lat, test_lng)
    print(f"\n【天气影响】")
    print(f"  天气: {weather['weather_status']}")
    print(f"  能见度: {weather['visibility']}")
    print(f"  综合影响: {weather['overall_impact']}")
    
    # 综合分析
    combined = analyzer.combined_analysis(test_lat, test_lng)
    print(f"\n【综合分析】")
    print(f"  威胁等级: {combined['threat_level']}")
    print(f"  建议: {combined['recommendation']}")
