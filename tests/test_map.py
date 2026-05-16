"""
地图模块测试

测试地图组件、图标管理器、覆盖层管理器的核心功能。
使用 pytest 框架，需要 pytest, pytest-qt 等依赖。
"""

import sys
import os
import json
import pytest

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from map.icon_manager import IconManager, IconData
from map.overlay import OverlayManager, TrackPoint, CombatRadius, HeatmapDataPoint


class TestIconManager:
    """测试 IconManager 类"""

    @pytest.fixture
    def icon_manager(self, tmp_path):
        """创建 IconManager 实例，使用临时图标目录"""
        icons_dir = tmp_path / 'icons'
        icons_dir.mkdir()

        # 创建测试 SVG 文件
        for icon_type in ['warship', 'submarine', 'base']:
            svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle fill="#FF0000" cx="16" cy="16" r="10"/></svg>'
            (icons_dir / f'{icon_type}.svg').write_text(svg_content)

        return IconManager(icons_dir=str(icons_dir))

    def test_load_svg_icons(self, icon_manager):
        """测试 SVG 图标加载"""
        uri = icon_manager.get_svg_data_uri('warship')
        assert uri is not None
        assert uri.startswith('data:image/svg+xml;charset=utf-8,')
        assert len(uri) > 100

    def test_get_nonexistent_svg(self, icon_manager):
        """测试获取不存在的 SVG"""
        uri = icon_manager.get_svg_data_uri('nonexistent')
        assert uri is None

    def test_create_icon_config(self, icon_manager):
        """测试创建图标配置"""
        icon_data = IconData(
            icon_type='warship',
            icon_id='ship_001',
            name='辽宁舰',
            lng=121.5,
            lat=31.2,
            unit_id='unit_navy',
            unit_name='北海舰队',
            status='active',
            extra_data={'tonnage': 60000}
        )

        config = icon_manager.create_icon_config(icon_data)

        assert config['type'] == 'warship'
        assert config['lng'] == 121.5
        assert config['lat'] == 31.2
        assert config['data']['name'] == '辽宁舰'
        assert config['data']['unit_name'] == '北海舰队'
        assert config['data']['tonnage'] == 60000

    def test_cluster_by_region_low_zoom(self, icon_manager):
        """测试低缩放级别聚合"""
        icons = [
            {'type': 'warship', 'lng': 121.0, 'lat': 31.0, 'data': {}},
            {'type': 'warship', 'lng': 121.5, 'lat': 31.5, 'data': {}},
            {'type': 'submarine', 'lng': 130.0, 'lat': 35.0, 'data': {}},
        ]

        clustered = icon_manager.get_cluster(zoom_level=4, icons=icons)

        # 低缩放应该聚合
        assert len(clustered) < len(icons)

    def test_cluster_by_region_high_zoom(self, icon_manager):
        """测试高缩放级别不聚合"""
        icons = [
            {'type': 'warship', 'lng': 121.0, 'lat': 31.0, 'data': {}},
            {'type': 'warship', 'lng': 121.5, 'lat': 31.5, 'data': {}},
        ]

        clustered = icon_manager.get_cluster(zoom_level=15, icons=icons)

        # 高缩放不应聚合
        assert len(clustered) == len(icons)

    def test_get_icon_stats(self, icon_manager):
        """测试图标统计"""
        icons = [
            {'type': 'warship', 'lng': 121.0, 'lat': 31.0, 'data': {}},
            {'type': 'warship', 'lng': 122.0, 'lat': 32.0, 'data': {}},
            {'type': 'submarine', 'lng': 130.0, 'lat': 35.0, 'data': {}},
        ]

        stats = icon_manager.get_icon_stats(icons)

        assert stats['warship'] == 2
        assert stats['submarine'] == 1
        assert stats['total'] == 3

    def test_filter_icons_by_type(self, icon_manager):
        """测试按类型过滤图标"""
        icons = [
            {'type': 'warship', 'lng': 121.0, 'lat': 31.0, 'data': {}},
            {'type': 'submarine', 'lng': 130.0, 'lat': 35.0, 'data': {}},
            {'type': 'warship', 'lng': 122.0, 'lat': 32.0, 'data': {}},
        ]

        filtered = icon_manager.filter_icons_by_type(icons, 'warship')

        assert len(filtered) == 2
        assert all(icon['type'] == 'warship' for icon in filtered)

    def test_filter_icons_by_bounds(self, icon_manager):
        """测试按边界过滤图标"""
        icons = [
            {'type': 'warship', 'lng': 121.0, 'lat': 31.0, 'data': {}},
            {'type': 'submarine', 'lng': 130.0, 'lat': 35.0, 'data': {}},
        ]

        filtered = icon_manager.filter_icons_by_bounds(
            icons,
            sw_lng=120, sw_lat=30,
            ne_lng=122, ne_lat=32
        )

        assert len(filtered) == 1
        assert filtered[0]['type'] == 'warship'


class TestOverlayManager:
    """测试 OverlayManager 类"""

    @pytest.fixture
    def overlay_manager(self):
        """创建 OverlayManager 实例"""
        return OverlayManager()

    def test_add_track(self, overlay_manager):
        """测试添加航迹线"""
        points = [
            TrackPoint(lng=121.5, lat=31.2, speed=20, heading=90),
            TrackPoint(lng=122.0, lat=31.5, speed=22, heading=95),
        ]

        track = overlay_manager.add_track('track_001', points, track_type='naval')

        assert track['id'] == 'track_001'
        assert len(track['points']) == 2
        assert track['color'] == '#00FFFF'  # naval 默认颜色

    def test_add_combat_radius(self, overlay_manager):
        """测试添加作战半径"""
        radius = overlay_manager.add_combat_radius(
            'radius_001',
            center_lng=121.5,
            center_lat=31.2,
            radius_km=200,
            color='#FF4444'
        )

        assert radius.center_lng == 121.5
        assert radius.radius_km == 200
        assert radius.color == '#FF4444'

    def test_add_heatmap_data(self, overlay_manager):
        """测试添加热力图数据"""
        points = [
            HeatmapDataPoint(lng=121.5, lat=31.2, intensity=80),
            HeatmapDataPoint(lng=122.0, lat=31.5, intensity=60),
        ]

        overlay_manager.add_heatmap_data(points)

        data = overlay_manager.get_heatmap_data()
        assert len(data) == 2
        assert data[0]['count'] == 80

    def test_remove_track(self, overlay_manager):
        """测试移除航迹线"""
        points = [TrackPoint(lng=121.5, lat=31.2)]
        overlay_manager.add_track('track_001', points)

        result = overlay_manager.remove_track('track_001')
        assert result is True
        assert overlay_manager.get_track('track_001') is None

    def test_remove_nonexistent_track(self, overlay_manager):
        """测试移除不存在的航迹线"""
        result = overlay_manager.remove_track('nonexistent')
        assert result is False

    def test_clear_tracks(self, overlay_manager):
        """测试清除所有航迹线"""
        points = [TrackPoint(lng=121.5, lat=31.2)]
        overlay_manager.add_track('track_001', points)
        overlay_manager.add_track('track_002', points)

        overlay_manager.clear_tracks()

        assert len(overlay_manager.get_all_tracks()) == 0

    def test_export_import_config(self, overlay_manager):
        """测试配置导出和导入"""
        # 添加测试数据
        points = [TrackPoint(lng=121.5, lat=31.2)]
        overlay_manager.add_track('track_001', points, track_type='naval')

        overlay_manager.add_combat_radius(
            'radius_001',
            center_lng=121.5,
            center_lat=31.2,
            radius_km=200
        )

        overlay_manager.add_heatmap_data([
            HeatmapDataPoint(lng=121.5, lat=31.2, intensity=80)
        ])

        # 导出
        config = overlay_manager.export_config()

        # 创建新实例并导入
        new_manager = OverlayManager()
        new_manager.import_config(config)

        # 验证
        assert len(new_manager.get_all_tracks()) == 1
        assert len(new_manager.get_all_radii()) == 1
        assert len(new_manager.get_heatmap_data()) == 1

    def test_visibility_settings(self, overlay_manager):
        """测试可见性设置"""
        overlay_manager.set_heatmap_visible(False)
        overlay_manager.set_tracks_visible(False)
        overlay_manager.set_radius_visible(False)

        assert overlay_manager.is_heatmap_visible() is False
        assert overlay_manager.is_tracks_visible() is False
        assert overlay_manager.is_radius_visible() is False


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
