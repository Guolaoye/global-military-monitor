# -*- coding: utf-8 -*-
"""
时间轴管理器 - 管理单位位置历史记录和时间点快照
支持历史轨迹查询和时间线导出
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json

from src.db.connection import get_cursor


class TimelineManager:
    """
    时间轴管理器
    负责从数据库加载位置历史，支持时间点快照查询
    """
    
    def __init__(self):
        self.positions_cache = []
        self.time_range = None
    
    def load_positions(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        从数据库加载位置记录，按报告时间排序
        
        Args:
            limit: 最大返回记录数
            
        Returns:
            位置记录列表，每条记录包含unit信息
        """
        try:
            with get_cursor() as cursor:
                # 查询位置表和单位表联合数据
                query = '''
                    SELECT 
                        p.id as position_id,
                        p.unit_id,
                        p.latitude,
                        p.longitude,
                        p.altitude,
                        p.heading,
                        p.speed,
                        p.reported_at,
                        u.name as unit_name,
                        u.unit_type,
                        u.country_id,
                        u.status as unit_status,
                        c.name as country_name
                    FROM positions p
                    LEFT JOIN units u ON p.unit_id = u.id
                    LEFT JOIN countries c ON u.country_id = c.id
                    ORDER BY p.reported_at ASC
                    LIMIT %s
                '''
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                
                self.positions_cache = []
                for row in rows:
                    self.positions_cache.append({
                        'position_id': row[0],
                        'unit_id': row[1],
                        'latitude': float(row[2]) if row[2] else 0.0,
                        'longitude': float(row[3]) if row[3] else 0.0,
                        'altitude': float(row[4]) if row[4] else 0.0,
                        'heading': float(row[5]) if row[5] else 0.0,
                        'speed': float(row[6]) if row[6] else 0.0,
                        'reported_at': str(row[7]) if row[7] else '',
                        'unit_name': row[8] or '未知单位',
                        'unit_type': row[9] or '未知类型',
                        'country_id': row[10],
                        'unit_status': row[11] or 'unknown',
                        'country_name': row[12] or '未知国家'
                    })
                
                # 计算时间范围
                if self.positions_cache:
                    self.time_range = {
                        'start': self.positions_cache[0]['reported_at'],
                        'end': self.positions_cache[-1]['reported_at']
                    }
                
                return self.positions_cache
                
        except Exception as e:
            print(f"加载位置数据失败: {e}")
            return []
    
    def get_positions_at_time(self, timestamp: str) -> List[Dict[str, Any]]:
        """
        获取指定时间点的位置快照
        对于该时间点之前最后报告的位置作为快照位置
        
        Args:
            timestamp: ISO格式时间戳字符串
            
        Returns:
            该时间点的位置快照列表
        """
        if not self.positions_cache:
            self.load_positions()
        
        # 按单位分组，获取最近的位置
        unit_latest_positions = {}
        
        for pos in self.positions_cache:
            if pos['reported_at'] <= timestamp:
                unit_id = pos['unit_id']
                # 同单位的保留最新的
                if unit_id not in unit_latest_positions:
                    unit_latest_positions[unit_id] = pos
                elif pos['reported_at'] > unit_latest_positions[unit_id]['reported_at']:
                    unit_latest_positions[unit_id] = pos
        
        return list(unit_latest_positions.values())
    
    def get_unit_trajectory(
        self, 
        unit_id: int, 
        start_time: Optional[str] = None, 
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取特定单位在时间范围内的轨迹
        
        Args:
            unit_id: 单位ID
            start_time: 开始时间（ISO格式），None表示从头开始
            end_time: 结束时间（ISO格式），None表示到最新
            
        Returns:
            单位的轨迹点列表
        """
        try:
            with get_cursor() as cursor:
                # 构建动态查询
                query = '''
                    SELECT 
                        p.latitude,
                        p.longitude,
                        p.altitude,
                        p.heading,
                        p.speed,
                        p.reported_at
                    FROM positions p
                    WHERE p.unit_id = %s
                '''
                params = [unit_id]
                
                if start_time:
                    query += " AND p.reported_at >= %s"
                    params.append(start_time)
                
                if end_time:
                    query += " AND p.reported_at <= %s"
                    params.append(end_time)
                
                query += " ORDER BY p.reported_at ASC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                trajectory = []
                for row in rows:
                    trajectory.append({
                        'latitude': float(row[0]) if row[0] else 0.0,
                        'longitude': float(row[1]) if row[1] else 0.0,
                        'altitude': float(row[2]) if row[2] else 0.0,
                        'heading': float(row[3]) if row[3] else 0.0,
                        'speed': float(row[4]) if row[4] else 0.0,
                        'reported_at': str(row[5]) if row[5] else ''
                    })
                
                return trajectory
                
        except Exception as e:
            print(f"获取单位轨迹失败: {e}")
            return []
    
    def export_timeline_json(self) -> Dict[str, Any]:
        """
        导出完整时间线数据为JSON格式
        
        Returns:
            包含时间线元数据和位置数据的字典
        """
        if not self.positions_cache:
            self.load_positions()
        
        # 构建导出结构
        export_data = {
            'export_time': datetime.now().isoformat(),
            'time_range': self.time_range,
            'total_records': len(self.positions_cache),
            'unique_units': len(set(p['unit_id'] for p in self.positions_cache)),
            'positions': self.positions_cache
        }
        
        return export_data
    
    def get_time_points(self, interval_minutes: int = 60) -> List[str]:
        """
        获取等间隔的时间点列表
        
        Args:
            interval_minutes: 时间间隔（分钟）
            
        Returns:
            ISO格式时间戳字符串列表
        """
        if not self.positions_cache or not self.time_range:
            return []
        
        time_points = []
        start = datetime.fromisoformat(self.time_range['start'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(self.time_range['end'].replace('Z', '+00:00'))
        
        current = start
        while current <= end:
            time_points.append(current.isoformat())
            current += timedelta(minutes=interval_minutes)
        
        return time_points


class PositionHistoryManager:
    """
    位置历史管理器 - 扩展功能
    提供轨迹分析、可视化数据准备等功能
    """
    
    def __init__(self):
        self.timeline_manager = TimelineManager()
    
    def calculate_movement_stats(self, unit_id: int) -> Dict[str, Any]:
        """
        计算单位移动统计信息
        
        Args:
            unit_id: 单位ID
            
        Returns:
            包含移动距离、平均速度、最大速度等统计信息
        """
        trajectory = self.timeline_manager.get_unit_trajectory(unit_id)
        
        if len(trajectory) < 2:
            return {
                'total_distance_km': 0,
                'avg_speed_kmh': 0,
                'max_speed_kmh': 0,
                'duration_hours': 0,
                'start_point': None,
                'end_point': None
            }
        
        total_distance = 0.0
        max_speed = 0.0
        total_time_delta = timedelta()
        
        for i in range(1, len(trajectory)):
            prev = trajectory[i-1]
            curr = trajectory[i]
            
            # 计算距离
            dist = self._haversine_distance(
                prev['latitude'], prev['longitude'],
                curr['latitude'], curr['longitude']
            )
            total_distance += dist
            
            # 计算最大速度
            if curr['speed'] > max_speed:
                max_speed = curr['speed']
            
            # 计算时间差
            try:
                t1 = datetime.fromisoformat(prev['reported_at'].replace('Z', '+00:00'))
                t2 = datetime.fromisoformat(curr['reported_at'].replace('Z', '+00:00'))
                total_time_delta += (t2 - t1)
            except:
                pass
        
        avg_speed = total_distance / max(1, total_time_delta.total_seconds() / 3600)
        
        return {
            'total_distance_km': round(total_distance, 2),
            'avg_speed_kmh': round(avg_speed, 2),
            'max_speed_kmh': round(max_speed, 2),
            'duration_hours': round(total_time_delta.total_seconds() / 3600, 2),
            'start_point': trajectory[0],
            'end_point': trajectory[-1],
            'trajectory_points': len(trajectory)
        }
    
    def get_confrontation_evolution(
        self, 
        unit_ids: List[int],
        time_interval_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取多个单位之间的对峙演变历史
        
        Args:
            unit_ids: 单位ID列表
            time_interval_minutes: 时间间隔
            
        Returns:
            时间序列的距离变化数据
        """
        # 获取所有单位的轨迹
        all_trajectories = {}
        for uid in unit_ids:
            all_trajectories[uid] = self.timeline_manager.get_unit_trajectory(uid)
        
        # 收集所有时间点
        all_times = set()
        for traj in all_trajectories.values():
            for point in traj:
                all_times.add(point['reported_at'])
        
        sorted_times = sorted(all_times)
        
        # 采样等间隔时间点
        evolution = []
        interval_count = max(1, len(sorted_times) // 100)  # 最多100个点
        
        for i in range(0, len(sorted_times), interval_count):
            timestamp = sorted_times[i]
            snapshot = {
                'timestamp': timestamp,
                'units': {}
            }
            
            for uid in unit_ids:
                traj = all_trajectories.get(uid, [])
                # 找到该时间点之前最近的位置
                pos = None
                for point in reversed(traj):
                    if point['reported_at'] <= timestamp:
                        pos = point
                        break
                
                if pos:
                    snapshot['units'][str(uid)] = {
                        'latitude': pos['latitude'],
                        'longitude': pos['longitude']
                    }
            
            # 计算单位间距离
            if len(snapshot['units']) >= 2:
                unit_list = list(snapshot['units'].values())
                distances = []
                for i in range(len(unit_list)):
                    for j in range(i+1, len(unit_list)):
                        dist = self._haversine_distance(
                            unit_list[i]['latitude'], unit_list[i]['longitude'],
                            unit_list[j]['latitude'], unit_list[j]['longitude']
                        )
                        distances.append(dist)
                snapshot['min_distance_km'] = min(distances) if distances else None
                snapshot['avg_distance_km'] = sum(distances) / len(distances) if distances else None
            
            evolution.append(snapshot)
        
        return evolution
    
    def prepare_visualization_data(self, unit_id: int) -> Dict[str, Any]:
        """
        准备可视化所需的数据格式
        
        Args:
            unit_id: 单位ID
            
        Returns:
            适合前端可视化的数据格式
        """
        trajectory = self.timeline_manager.get_unit_trajectory(unit_id)
        
        coordinates = []
        timestamps = []
        speeds = []
        
        for point in trajectory:
            coordinates.append([point['longitude'], point['latitude']])
            timestamps.append(point['reported_at'])
            speeds.append(point['speed'])
        
        stats = self.calculate_movement_stats(unit_id)
        
        return {
            'trajectory': {
                'coordinates': coordinates,
                'timestamps': timestamps,
                'speeds': speeds
            },
            'statistics': stats,
            'bounds': self._calculate_bounds(coordinates) if coordinates else None
        }
    
    def _haversine_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        使用Haversine公式计算两点间距离（公里）
        """
        import math
        
        R = 6371.0  # 地球半径（公里）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 +             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_bounds(self, coordinates: List[List[float]]) -> Dict[str, float]:
        """计算坐标边界"""
        if not coordinates:
            return {}
        
        lons = [c[0] for c in coordinates]
        lats = [c[1] for c in coordinates]
        
        return {
            'min_lon': min(lons),
            'max_lon': max(lons),
            'min_lat': min(lats),
            'max_lat': max(lats)
        }


if __name__ == '__main__':
    # 测试代码
    manager = TimelineManager()
    positions = manager.load_positions(limit=100)
    print(f"加载了 {len(positions)} 条位置记录")
    
    if positions:
        # 测试获取时间点快照
        snapshot = manager.get_positions_at_time(positions[-1]['reported_at'])
        print(f"最新时间点快照包含 {len(snapshot)} 个单位")
        
        # 测试导出
        export = manager.export_timeline_json()
        print(f"导出数据包含 {export['total_records']} 条记录")
