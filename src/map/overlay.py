"""
地图覆盖层管理器 - 航迹线、作战半径、热力图

负责管理高德地图上的高级可视化图层：
1. 航迹线 - 显示舰艇/飞机的移动轨迹
2. 作战半径 - 显示以某点为中心的威慑/作战范围
3. 热力图 - 显示军事活动的热度分布
"""

import json
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class TrackPoint:
    """航迹点"""
    lng: float
    lat: float
    timestamp: Optional[int] = None  # Unix 时间戳
    speed: Optional[float] = None    # 速度 (km/h)
    heading: Optional[float] = None   # 航向角 (度)


@dataclass
class CombatRadius:
    """作战半径配置"""
    center_lng: float
    center_lat: float
    radius_km: float
    color: str = '#FF4444'
    fill_opacity: float = 0.15
    stroke_opacity: float = 0.8
    label: str = ''


@dataclass
class HeatmapDataPoint:
    """热力图数据点"""
    lng: float
    lat: float
    intensity: float = 1.0  # 强度 0-100


class OverlayManager:
    """
    地图覆盖层管理器

    提供统一的接口管理航迹线、作战半径、热力图等高级图层。
    """

    # 默认颜色配置
    DEFAULT_COLORS = {
        'naval': '#00FFFF',      # 海军航迹 - 青色
        'air': '#00CCFF',        # 空军航迹 - 蓝色
        'red': '#FF4444',        # 红色警告
        'orange': '#FF8800',     # 橙色
        'yellow': '#FFCC00',     # 黄色
        'purple': '#CC00CC',     # 紫色
        'green': '#00FF88'       # 绿色
    }

    def __init__(self):
        """初始化覆盖层管理器"""
        self._tracks: Dict[str, Any] = {}      # 存储所有航迹线
        self._radii: Dict[str, Any] = {}       # 存储所有作战半径
        self._heatmap_data: List[Dict[str, Any]] = []  # 热力图数据
        self._is_heatmap_visible = False
        self._is_tracks_visible = True
        self._is_radius_visible = True

    # ==================== 航迹线管理 ====================

    def add_track(self, track_id: str, points: List[TrackPoint],
                  color: Optional[str] = None,
                  track_type: str = 'naval',
                  width: int = 2) -> Dict[str, Any]:
        """
        添加航迹线

        Args:
            track_id: 航迹唯一ID
            points: 航迹点列表
            color: 线条颜色，默认根据 track_type 自动选择
            track_type: 航迹类型 ('naval', 'air', 'red', 'orange', 'yellow', 'purple', 'green')
            width: 线条宽度

        Returns:
            航迹线配置字典
        """
        if color is None:
            color = self.DEFAULT_COLORS.get(track_type, self.DEFAULT_COLORS['naval'])

        # 转换为 JS 友好的格式
        track_config = {
            'id': track_id,
            'points': [
                {'lng': p.lng, 'lat': p.lat}
                for p in points
            ],
            'color': color,
            'width': width,
            'type': track_type,
            'point_count': len(points)
        }

        self._tracks[track_id] = track_config
        print(f"[Overlay] 添加航迹线: {track_id}, 点数: {len(points)}")

        return track_config

    def remove_track(self, track_id: str) -> bool:
        """
        移除航迹线

        Args:
            track_id: 航迹ID

        Returns:
            是否成功移除
        """
        if track_id in self._tracks:
            del self._tracks[track_id]
            print(f"[Overlay] 移除航迹线: {track_id}")
            return True
        return False

    def get_track(self, track_id: str) -> Optional[Dict[str, Any]]:
        """获取航迹线配置"""
        return self._tracks.get(track_id)

    def get_all_tracks(self) -> List[Dict[str, Any]]:
        """获取所有航迹线"""
        return list(self._tracks.values())

    def clear_tracks(self):
        """清除所有航迹线"""
        self._tracks.clear()
        print("[Overlay] 清除所有航迹线")

    def update_track(self, track_id: str, new_points: List[TrackPoint]):
        """
        更新航迹线（追加新点）

        Args:
            track_id: 航迹ID
            new_points: 新增的航迹点
        """
        if track_id not in self._tracks:
            print(f"[Overlay] 航迹线不存在: {track_id}")
            return

        track = self._tracks[track_id]
        for p in new_points:
            track['points'].append({'lng': p.lng, 'lat': p.lat})
        track['point_count'] = len(track['points'])

    # ==================== 作战半径管理 ====================

    def add_combat_radius(self, radius_id: str,
                          center_lng: float, center_lat: float,
                          radius_km: float,
                          color: Optional[str] = None,
                          fill_opacity: float = 0.15,
                          label: str = '') -> CombatRadius:
        """
        添加作战半径

        Args:
            radius_id: 半径唯一ID
            center_lng: 中心点经度
            center_lat: 中心点纬度
            radius_km: 半径（公里）
            color: 颜色，默认红色
            fill_opacity: 填充透明度
            label: 标签文字

        Returns:
            作战半径配置对象
        """
        if color is None:
            color = self.DEFAULT_COLORS['red']

        radius_config = CombatRadius(
            center_lng=center_lng,
            center_lat=center_lat,
            radius_km=radius_km,
            color=color,
            fill_opacity=fill_opacity,
            label=label
        )

        self._radii[radius_id] = radius_config
        print(f"[Overlay] 添加作战半径: {radius_id}, 范围: {radius_km}km")

        return radius_config

    def remove_combat_radius(self, radius_id: str) -> bool:
        """移除作战半径"""
        if radius_id in self._radii:
            del self._radii[radius_id]
            print(f"[Overlay] 移除作战半径: {radius_id}")
            return True
        return False

    def get_combat_radius(self, radius_id: str) -> Optional[CombatRadius]:
        """获取作战半径配置"""
        return self._radii.get(radius_id)

    def get_all_radii(self) -> List[CombatRadius]:
        """获取所有作战半径"""
        return list(self._radii.values())

    def clear_radii(self):
        """清除所有作战半径"""
        self._radii.clear()
        print("[Overlay] 清除所有作战半径")

    # ==================== 热力图管理 ====================

    def add_heatmap_data(self, data_points: List[HeatmapDataPoint]):
        """
        添加热力图数据点

        Args:
            data_points: 热力数据点列表
        """
        for point in data_points:
            self._heatmap_data.append({
                'lng': point.lng,
                'lat': point.lat,
                'count': point.intensity
            })

        print(f"[Overlay] 添加热力图数据点: {len(data_points)}, 总计: {len(self._heatmap_data)}")

    def set_heatmap_data(self, data_points: List[HeatmapDataPoint]):
        """
        设置热力图数据（替换现有数据）

        Args:
            data_points: 热力数据点列表
        """
        self._heatmap_data = [
            {'lng': p.lng, 'lat': p.lat, 'count': p.intensity}
            for p in data_points
        ]
        print(f"[Overlay] 设置热力图数据: {len(self._heatmap_data)} 点")

    def clear_heatmap_data(self):
        """清除热力图数据"""
        self._heatmap_data.clear()
        print("[Overlay] 清除热力图数据")

    def get_heatmap_data(self) -> List[Dict[str, Any]]:
        """获取热力图数据"""
        return self._heatmap_data

    def set_heatmap_visible(self, visible: bool):
        """设置热力图可见性"""
        self._is_heatmap_visible = visible
        print(f"[Overlay] 热力图可见性: {visible}")

    def set_tracks_visible(self, visible: bool):
        """设置航迹线可见性"""
        self._is_tracks_visible = visible
        print(f"[Overlay] 航迹线可见性: {visible}")

    def set_radius_visible(self, visible: bool):
        """设置作战半径可见性"""
        self._is_radius_visible = visible
        print(f"[Overlay] 作战半径可见性: {visible}")

    def is_heatmap_visible(self) -> bool:
        """热力图是否可见"""
        return self._is_heatmap_visible

    def is_tracks_visible(self) -> bool:
        """航迹线是否可见"""
        return self._is_tracks_visible

    def is_radius_visible(self) -> bool:
        """作战半径是否可见"""
        return self._is_radius_visible

    # ==================== 批量操作 ====================

    def clear_all(self):
        """清除所有覆盖层数据"""
        self.clear_tracks()
        self.clear_radii()
        self.clear_heatmap_data()
        print("[Overlay] 清除所有覆盖层")

    def export_config(self) -> Dict[str, Any]:
        """
        导出所有覆盖层配置为 JSON 格式

        Returns:
            包含所有覆盖层配置的字典
        """
        return {
            'tracks': [
                {
                    'id': t['id'],
                    'points': t['points'],
                    'color': t['color'],
                    'width': t['width'],
                    'type': t['type']
                }
                for t in self._tracks.values()
            ],
            'radii': [
                {
                    'id': r_id,
                    'center_lng': r.center_lng,
                    'center_lat': r.center_lat,
                    'radius_km': r.radius_km,
                    'color': r.color,
                    'label': r.label
                }
                for r_id, r in self._radii.items()
            ],
            'heatmap': self._heatmap_data,
            'visibility': {
                'heatmap': self._is_heatmap_visible,
                'tracks': self._is_tracks_visible,
                'radius': self._is_radius_visible
            }
        }

    def import_config(self, config: Dict[str, Any]):
        """
        从 JSON 配置导入覆盖层数据

        Args:
            config: 覆盖层配置字典
        """
        # 导入航迹线
        if 'tracks' in config:
            for track in config['tracks']:
                self._tracks[track['id']] = track

        # 导入作战半径
        if 'radii' in config:
            for radius_data in config['radii']:
                radius = CombatRadius(**radius_data)
                self._radii[radius_data['id']] = radius

        # 导入热力图数据
        if 'heatmap' in config:
            self._heatmap_data = config['heatmap']

        # 导入可见性设置
        if 'visibility' in config:
            vis = config['visibility']
            self._is_heatmap_visible = vis.get('heatmap', False)
            self._is_tracks_visible = vis.get('tracks', True)
            self._is_radius_visible = vis.get('radius', True)

        print("[Overlay] 从配置导入覆盖层数据")


# 模块自测
if __name__ == '__main__':
    manager = OverlayManager()

    # 测试添加航迹线
    track_points = [
        TrackPoint(lng=121.5, lat=31.2, speed=20, heading=90),
        TrackPoint(lng=122.0, lat=31.5, speed=22, heading=95),
        TrackPoint(lng=122.5, lat=31.8, speed=25, heading=100),
    ]
    track = manager.add_track('ship_001', track_points, track_type='naval')
    print(f"添加航迹线: {track['id']}")

    # 测试添加作战半径
    radius = manager.add_combat_radius(
        'radius_001',
        center_lng=121.5,
        center_lat=31.2,
        radius_km=200,
        color='#FF4444',
        label='辽宁舰作战半径'
    )
    print(f"添加作战半径: {radius.radius_km}km")

    # 测试添加热力图数据
    heatmap_points = [
        HeatmapDataPoint(lng=121.5, lat=31.2, intensity=80),
        HeatmapDataPoint(lng=122.0, lat=31.5, intensity=60),
        HeatmapDataPoint(lng=122.5, lat=31.8, intensity=40),
    ]
    manager.add_heatmap_data(heatmap_points)
    print(f"热力图数据点: {len(manager.get_heatmap_data())}")

    # 测试导出配置
    config = manager.export_config()
    print(f"导出配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
