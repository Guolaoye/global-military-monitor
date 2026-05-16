"""
图标管理器 - 从数据库读取军事目标数据，生成高德地图图标

负责：
1. 从数据库模型读取图标数据
2. 加载 SVG 图标文件
3. 生成高德地图 Marker 配置
4. 实现缩放级别的聚合算法
"""

import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class IconData:
    """图标数据类"""
    icon_type: str          # 图标类型
    icon_id: str           # 图标唯一ID
    name: str              # 名称
    lng: float              # 经度
    lat: float              # 纬度
    unit_id: str            # 所属单位ID
    unit_name: str          # 所属单位名称
    status: str             # 状态
    extra_data: Dict[str, Any]  # 额外数据


class IconManager:
    """
    军事目标图标管理器

    从数据库读取图标数据，生成符合高德地图规范的图标配置。
    支持 SVG 图标、data-uri 编码、缩放级别聚合。
    """

    # 8类军事目标类型
    ICON_TYPES = [
        'warship',       # 军舰
        'submarine',     # 潜艇
        'base',          # 军事基地
        'airport',       # 机场
        'ammunition',    # 弹药库
        'antiAircraft',  # 防空导弹
        'militaryAircraft',  # 军用飞机
        'oilDepot'       # 油库
    ]

    # 图标颜色配置
    ICON_COLORS = {
        'warship': '#FF4444',
        'submarine': '#CC00CC',
        'base': '#FF8800',
        'airport': '#4488FF',
        'ammunition': '#FF5500',
        'antiAircraft': '#FFCC00',
        'militaryAircraft': '#00CCFF',
        'oilDepot': '#884400'
    }

    # 中文名称映射
    ICON_NAMES_CN = {
        'warship': '军舰',
        'submarine': '潜艇',
        'base': '军事基地',
        'airport': '机场',
        'ammunition': '弹药库',
        'antiAircraft': '防空导弹',
        'militaryAircraft': '军用飞机',
        'oilDepot': '油库'
    }

    def __init__(self, icons_dir: Optional[str] = None):
        """
        初始化图标管理器

        Args:
            icons_dir: SVG 图标目录，默认使用 assets/icons/
        """
        if icons_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            icons_dir = os.path.join(current_dir, 'assets', 'icons')

        self._icons_dir = icons_dir
        self._svg_cache: Dict[str, str] = {}

        # 加载所有 SVG 图标
        self._load_svg_icons()

    def _load_svg_icons(self):
        """加载所有 SVG 图标到缓存"""
        for icon_type in self.ICON_TYPES:
            svg_path = os.path.join(self._icons_dir, f'{icon_type}.svg')
            if os.path.exists(svg_path):
                with open(svg_path, 'r', encoding='utf-8') as f:
                    self._svg_cache[icon_type] = f.read()
            else:
                print(f"[IconManager] SVG 文件不存在: {svg_path}")

    def get_svg_data_uri(self, icon_type: str) -> Optional[str]:
        """
        获取 SVG 图标的 data-uri

        Args:
            icon_type: 图标类型

        Returns:
            data:image/svg+xml;charset=utf-8,... 格式的 URI
        """
        if icon_type not in self._svg_cache:
            return None

        svg_content = self._svg_cache[icon_type]
        encoded = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
        return 'data:image/svg+xml;charset=utf-8,' + encoded

    def create_icon_config(self, icon_data: IconData) -> Dict[str, Any]:
        """
        创建单个图标的配置

        Args:
            icon_data: 图标数据

        Returns:
            符合高德地图规范的图标配置
        """
        return {
            'type': icon_data.icon_type,
            'lng': icon_data.lng,
            'lat': icon_data.lat,
            'data': {
                'id': icon_data.icon_id,
                'name': icon_data.name,
                'unit_id': icon_data.unit_id,
                'unit_name': icon_data.unit_name,
                'status': icon_data.status,
                **icon_data.extra_data
            }
        }

    def create_icons_from_db_models(self, db_models: List[Any]) -> List[Dict[str, Any]]:
        """
        从数据库模型列表创建图标配置列表

        Args:
            db_models: 数据库模型列表，每个模型需要有以下属性:
                - icon_type: str
                - icon_id: str
                - name: str
                - longitude: float
                - latitude: float
                - unit_id: str
                - unit_name: str
                - status: str

        Returns:
            图标配置列表
        """
        icons = []

        for model in db_models:
            icon_data = IconData(
                icon_type=getattr(model, 'icon_type', 'base'),
                icon_id=getattr(model, 'icon_id', str(getattr(model, 'id', ''))),
                name=getattr(model, 'name', '未知'),
                lng=float(getattr(model, 'longitude', 0)),
                lat=float(getattr(model, 'latitude', 0)),
                unit_id=getattr(model, 'unit_id', ''),
                unit_name=getattr(model, 'unit_name', ''),
                status=getattr(model, 'status', 'active'),
                extra_data={}
            )
            icons.append(self.create_icon_config(icon_data))

        return icons

    def get_cluster(self, zoom_level: int, icons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根据缩放级别计算图标聚合

        Args:
            zoom_level: 当前缩放级别 (4-18)
            icons: 所有图标列表

        Returns:
            聚合后的图标列表（聚合的图标会被合并）
        """
        if zoom_level < 6:
            # 低缩放级别：按大致区域聚合
            return self._cluster_by_region(icons, grid_size=10)
        elif zoom_level < 10:
            # 中缩放级别：按省份/海域聚合
            return self._cluster_by_region(icons, grid_size=5)
        elif zoom_level < 14:
            # 高缩放级别：按城市聚合
            return self._cluster_by_region(icons, grid_size=2)
        else:
            # 极高缩放级别：不聚合
            return icons

    def _cluster_by_region(self, icons: List[Dict[str, Any]], grid_size: float) -> List[Dict[str, Any]]:
        """
        按区域网格聚合图标

        Args:
            icons: 图标列表
            grid_size: 网格大小（经纬度度数）

        Returns:
            聚合后的图标列表
        """
        clusters: Dict[str, List[Dict[str, Any]]] = {}

        for icon in icons:
            lng = icon.get('lng', 0)
            lat = icon.get('lat', 0)

            # 计算网格键
            grid_x = int(lng / grid_size)
            grid_y = int(lat / grid_size)
            grid_key = f"{grid_x}_{grid_y}"

            if grid_key not in clusters:
                clusters[grid_key] = []
            clusters[grid_key].append(icon)

        result = []
        for grid_key, group in clusters.items():
            if len(group) == 1:
                result.append(group[0])
            else:
                # 聚合多个图标为中心点
                avg_lng = sum(g.get('lng', 0) for g in group) / len(group)
                avg_lat = sum(g.get('lat', 0) for g in group) / len(group)
                result.append({
                    'type': group[0].get('type', 'base'),
                    'lng': avg_lng,
                    'lat': avg_lat,
                    'data': {
                        'cluster_count': len(group),
                        'cluster': True,
                        'original_types': [g.get('type', 'base') for g in group]
                    }
                })

        return result

    def get_icon_stats(self, icons: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        获取图标统计信息

        Args:
            icons: 图标列表

        Returns:
            按类型统计的字典
        """
        stats = {icon_type: 0 for icon_type in self.ICON_TYPES}
        stats['total'] = 0

        for icon in icons:
            icon_type = icon.get('type', 'base')
            if icon_type in stats:
                stats[icon_type] += 1
                stats['total'] += 1

        return stats

    def filter_icons_by_type(self, icons: List[Dict[str, Any]], icon_type: str) -> List[Dict[str, Any]]:
        """
        按类型过滤图标

        Args:
            icons: 图标列表
            icon_type: 图标类型

        Returns:
            过滤后的图标列表
        """
        return [icon for icon in icons if icon.get('type') == icon_type]

    def filter_icons_by_bounds(self, icons: List[Dict[str, Any]],
                              sw_lng: float, sw_lat: float,
                              ne_lng: float, ne_lat: float) -> List[Dict[str, Any]]:
        """
        按边界过滤图标

        Args:
            icons: 图标列表
            sw_lng, sw_lat: 西南角经纬度
            ne_lng, ne_lat: 东北角经纬度

        Returns:
            在边界内的图标列表
        """
        return [
            icon for icon in icons
            if sw_lng <= icon.get('lng', 0) <= ne_lng
            and sw_lat <= icon.get('lat', 0) <= ne_lat
        ]

    def export_to_json(self, icons: List[Dict[str, Any]], output_path: str):
        """
        导出图标数据到 JSON 文件

        Args:
            icons: 图标列表
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(icons, f, ensure_ascii=False, indent=2)
        print(f"[IconManager] 导出图标数据到: {output_path}")

    def load_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """
        从 JSON 文件加载图标数据

        Args:
            json_path: JSON 文件路径

        Returns:
            图标列表
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            icons = json.load(f)
        print(f"[IconManager] 从 JSON 加载图标数据: {json_path}")
        return icons


# 模块自测
if __name__ == '__main__':
    manager = IconManager()

    # 测试获取 SVG data-uri
    for icon_type in IconManager.ICON_TYPES:
        uri = manager.get_svg_data_uri(icon_type)
        if uri:
            print(f"[{icon_type}] SVG URI 长度: {len(uri)}")
        else:
            print(f"[{icon_type}] SVG 未找到")

    # 测试创建图标配置
    test_icon = IconData(
        icon_type='warship',
        icon_id='ship_001',
        name='辽宁舰',
        lng=121.5,
        lat=31.2,
        unit_id='unit_navy_001',
        unit_name='北海舰队',
        status='active',
        extra_data={'tonnage': 60000}
    )

    config = manager.create_icon_config(test_icon)
    print(f"\n测试图标配置: {json.dumps(config, ensure_ascii=False, indent=2)}")

    # 测试聚合
    test_icons = [
        {'type': 'warship', 'lng': 121.0, 'lat': 31.0, 'data': {}},
        {'type': 'warship', 'lng': 121.5, 'lat': 31.5, 'data': {}},
        {'type': 'submarine', 'lng': 122.0, 'lat': 32.0, 'data': {}},
    ]
    clustered = manager.get_cluster(4, test_icons)
    print(f"\n聚合结果 (zoom=4): {len(clustered)} 个聚合点")

    clustered = manager.get_cluster(15, test_icons)
    print(f"聚合结果 (zoom=15): {len(clustered)} 个点")
