# -*- coding: utf-8 -*-
"""
受影响单位分析器 - 基于位置范围的影响分析
分析地图点击点附近一定范围内的单位，区分空中和地面火力单位
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import math
from typing import List, Dict, Any, Optional

from src.db.connection import get_cursor


class AffectedUnitsAnalyzer:
    """
    受影响单位分析器
    基于地理位置范围分析，找出指定范围内的所有单位
    支持空中单位（flight_range）和地面火力单位（weapon_range）区分
    """
    
    # 默认探测范围（公里）
    DEFAULT_SEARCH_RADIUS = 500.0
    
    def __init__(self):
        self.cached_units = None
        self.cached_positions = None
    
    def _get_all_units_with_positions(self) -> List[Dict[str, Any]]:
        """
        从数据库获取所有单位和当前位置信息
        
        Returns:
            单位列表，包含位置和能力参数
        """
        try:
            with get_cursor() as cursor:
                query = '''
                    SELECT 
                        u.id as unit_id,
                        u.name as unit_name,
                        u.unit_type,
                        u.country_id,
                        c.name as country_name,
                        e.id as equipment_id,
                        e.name as equipment_name,
                        e.equipment_type,
                        e.flight_range,
                        e.weapon_range,
                        e.speed as max_speed,
                        p.latitude,
                        p.longitude,
                        p.altitude,
                        p.heading,
                        p.speed,
                        p.reported_at
                    FROM units u
                    LEFT JOIN countries c ON u.country_id = c.id
                    LEFT JOIN equipment e ON u.id = e.id
                    LEFT JOIN LATERAL (
                        SELECT latitude, longitude, altitude, heading, speed, reported_at
                        FROM positions
                        WHERE unit_id = u.id
                        ORDER BY reported_at DESC
                        LIMIT 1
                    ) p ON true
                    WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
                '''
                cursor.execute(query)
                rows = cursor.fetchall()
                
                units = []
                for row in rows:
                    unit_type = row[2] or 'unknown'
                    flight_range = float(row[8]) if row[8] else 0.0
                    weapon_range = float(row[9]) if row[9] else 0.0
                    
                    units.append({
                        'unit_id': row[0],
                        'unit_name': row[1],
                        'unit_type': unit_type,
                        'country_id': row[3],
                        'country_name': row[4] or '未知',
                        'equipment_id': row[5],
                        'equipment_name': row[6],
                        'equipment_type': row[7],
                        'flight_range': flight_range,
                        'weapon_range': weapon_range,
                        'max_speed': float(row[10]) if row[10] else 0.0,
                        'latitude': float(row[11]) if row[11] else 0.0,
                        'longitude': float(row[12]) if row[12] else 0.0,
                        'altitude': float(row[13]) if row[13] else 0.0,
                        'heading': float(row[14]) if row[14] else 0.0,
                        'speed': float(row[15]) if row[15] else 0.0,
                        'reported_at': str(row[16]) if row[16] else ''
                    })
                
                return units
                
        except Exception as e:
            print(f"获取单位位置失败: {e}")
            return []
    
    def _calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        使用Haversine公式计算两点间地球表面距离（公里）
        
        Args:
            lat1, lon1: 第一个点的纬度和经度
            lat2, lon2: 第二个点的纬度和经度
            
        Returns:
            距离（公里）
        """
        R = 6371.0  # 地球平均半径（公里）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine公式
        a = math.sin(delta_lat / 2) ** 2 +             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def analyze_point(
        self, 
        lat: float, 
        lng: float, 
        radius_km: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        分析指定点的受影响单位
        
        Args:
            lat: 点击点纬度
            lng: 点击点经度
            radius_km: 搜索半径（公里），None使用默认值
            
        Returns:
            受影响单位列表，包含距离和能力信息
        """
        if radius_km is None:
            radius_km = self.DEFAULT_SEARCH_RADIUS
        
        units = self._get_all_units_with_positions()
        
        affected_units = []
        
        for unit in units:
            # 计算单位到点击点的距离
            distance = self._calculate_distance(
                lat, lng,
                unit['latitude'], unit['longitude']
            )
            
            # 判断单位是否在影响范围内
            unit_type = unit['unit_type'].lower()
            
            # 确定单位是否受影响的判断依据
            # 空中单位：飞行半径内
            # 地面火力：武器射程内
            # 其他单位：基础搜索半径内
            in_range = False
            range_type = None
            effective_range = radius_km
            
            # 检查是否为空中单位
            if unit_type in ['aircraft', 'air', 'plane', 'fighter', 'bomber', 
                            'helicopter', 'uav', '无人机', '飞机']:
                if unit['flight_range'] > 0:
                    effective_range = unit['flight_range']
                    if distance <= effective_range:
                        in_range = True
                        range_type = 'flight_range'
            
            # 检查是否为地面火力单位
            elif unit_type in ['artillery', 'missile', 'tank', 'spg', 
                              '火炮', '导弹', '坦克', '自行火炮']:
                if unit['weapon_range'] > 0:
                    effective_range = unit['weapon_range']
                    if distance <= effective_range:
                        in_range = True
                        range_type = 'weapon_range'
            
            # 其他单位使用基础搜索半径
            if not in_range and distance <= radius_km:
                in_range = True
                range_type = 'search_radius'
                effective_range = radius_km
            
            if in_range:
                affected_units.append({
                    'unit_id': unit['unit_id'],
                    'unit_name': unit['unit_name'],
                    'unit_type': unit['unit_type'],
                    'country_name': unit['country_name'],
                    'latitude': unit['latitude'],
                    'longitude': unit['longitude'],
                    'altitude': unit['altitude'],
                    'distance_km': round(distance, 2),
                    'effective_range_km': effective_range,
                    'range_type': range_type,
                    'flight_range': unit['flight_range'],
                    'weapon_range': unit['weapon_range'],
                    'heading': unit['heading'],
                    'speed': unit['speed'],
                    'capability_score': self._calculate_capability_score(unit, distance)
                })
        
        # 按距离排序
        affected_units.sort(key=lambda x: x['distance_km'])
        
        return affected_units
    
    def get_units_in_range(
        self, 
        unit_id: int, 
        range_km: float
    ) -> List[Dict[str, Any]]:
        """
        获取指定单位影响范围内的其他单位
        
        Args:
            unit_id: 源单位ID
            range_km: 作用范围（公里）
            
        Returns:
            范围内单位列表
        """
        # 获取源单位位置
        try:
            with get_cursor() as cursor:
                cursor.execute('''
                    SELECT latitude, longitude
                    FROM positions
                    WHERE unit_id = %s
                    ORDER BY reported_at DESC
                    LIMIT 1
                ''', (unit_id,))
                result = cursor.fetchone()
                
                if not result:
                    return []
                
                src_lat = float(result[0])
                src_lng = float(result[1])
                
        except Exception as e:
            print(f"获取源单位位置失败: {e}")
            return []
        
        # 分析该范围内的所有单位
        return self.analyze_point(src_lat, src_lng, range_km)
    
    def _calculate_capability_score(
        self, 
        unit: Dict[str, Any], 
        distance_km: float
    ) -> float:
        """
        计算单位在给定距离的效能评分
        
        评分考虑因素：
        - 距离因素：距离越近效能越高
        - 单位类型能力
        - 射程覆盖
        
        Args:
            unit: 单位信息字典
            distance_km: 到目标点的距离
            
        Returns:
            0-100的效能评分
        """
        base_score = 50.0
        
        # 距离评分（越近分数越高）
        if distance_km <= 50:
            distance_factor = 1.0
        elif distance_km <= 200:
            distance_factor = 0.8
        elif distance_km <= 500:
            distance_factor = 0.5
        else:
            distance_factor = 0.2
        
        # 能力加成
        capability_bonus = 0.0
        
        unit_type = unit.get('unit_type', '').lower()
        
        if unit_type in ['aircraft', 'air', 'fighter', 'bomber']:
            capability_bonus += 30.0  # 空中优势
        elif unit_type in ['missile']:
            capability_bonus += 40.0  # 精确打击
        elif unit_type in ['artillery', 'spg']:
            capability_bonus += 25.0  # 火力支援
        elif unit_type in ['tank']:
            capability_bonus += 15.0  # 地面突击
        
        # 射程覆盖检查
        effective_range = unit.get('flight_range', 0) or unit.get('weapon_range', 0)
        if effective_range > 0 and distance_km <= effective_range:
            capability_bonus += 20.0
        
        final_score = base_score * distance_factor + capability_bonus
        return min(100.0, max(0.0, final_score))
    
    def get_threat_matrix(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        生成威胁矩阵分析
        
        Args:
            lat: 分析点纬度
            lng: 分析点经度
            
        Returns:
            威胁矩阵字典，包含分类统计
        """
        affected = self.analyze_point(lat, lng)
        
        # 按国家和类型分组
        threats_by_country = {}
        threats_by_type = {
            'aircraft': [],
            'artillery': [],
            'missile': [],
            'other': []
        }
        
        for unit in affected:
            country = unit.get('country_name', '未知')
            unit_type = unit.get('unit_type', '').lower()
            
            # 国家分组
            if country not in threats_by_country:
                threats_by_country[country] = {
                    'count': 0,
                    'units': [],
                    'total_capability': 0
                }
            threats_by_country[country]['count'] += 1
            threats_by_country[country]['units'].append(unit)
            threats_by_country[country]['total_capability'] += unit.get('capability_score', 0)
            
            # 类型分组
            if unit_type in ['aircraft', 'air', 'plane', 'fighter', 'bomber', 'helicopter']:
                threats_by_type['aircraft'].append(unit)
            elif unit_type in ['missile']:
                threats_by_type['missile'].append(unit)
            elif unit_type in ['artillery', 'spg', 'tank']:
                threats_by_type['artillery'].append(unit)
            else:
                threats_by_type['other'].append(unit)
        
        # 计算威胁等级
        total_threat = sum(t['total_capability'] for t in threats_by_country.values())
        
        if total_threat >= 500:
            threat_level = '极高'
        elif total_threat >= 300:
            threat_level = '高'
        elif total_threat >= 150:
            threat_level = '中'
        else:
            threat_level = '低'
        
        return {
            'analysis_point': {'latitude': lat, 'longitude': lng},
            'total_affected_units': len(affected),
            'threat_level': threat_level,
            'total_threat_score': total_threat,
            'by_country': threats_by_country,
            'by_type': threats_by_type,
            'most_dangerous': affected[:5] if affected else []
        }


if __name__ == '__main__':
    # 测试代码
    analyzer = AffectedUnitsAnalyzer()
    
    # 测试点：假设分析某坐标点
    test_lat, test_lng = 39.9042, 116.4074  # 北京
    
    print(f"分析坐标点: ({test_lat}, {test_lng})")
    
    affected = analyzer.analyze_point(test_lat, test_lng, radius_km=300)
    print(f"影响范围内单位数: {len(affected)}")
    
    if affected:
        print("\n前5个受影响单位:")
        for unit in affected[:5]:
            print(f"  - {unit['unit_name']} ({unit['unit_type']})")
            print(f"    距离: {unit['distance_km']:.1f}km, 效能评分: {unit['capability_score']:.1f}")
    
    # 测试威胁矩阵
    print("\n威胁矩阵分析:")
    matrix = analyzer.get_threat_matrix(test_lat, test_lng)
    print(f"  威胁等级: {matrix['threat_level']}")
    print(f"  受影响单位总数: {matrix['total_affected_units']}")
