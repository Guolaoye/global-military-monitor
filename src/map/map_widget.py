"""
地图态势展示模块 - PyQt5 WebEngine 集成

负责加载高德地图 JSAPI，通过 QWebChannel 实现 Python-JS 双向通信。
支持图标管理、图层控制、航迹线、作战半径、热力图等高级功能。
"""

import os
import json
from typing import List, Dict, Optional, Any
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QTimer
from PyQt5.QtWebEngineCore import QWebEngineSettings


class MapBridge(QObject):
    """
    Python-JS 通信桥接对象

    将此对象注册到 QWebChannel，使 JavaScript 可以调用 Python 方法，
    同时 Python 可以通过 runJavaScript 调用 JS 函数。
    """

    # 信号：图标被点击
    # icon_type: str - 图标类型 (warship, submarine, base, etc.)
    # unit_id: str - 单位ID
    icon_clicked = pyqtSignal(str, str)

    # 信号：地图加载完成
    map_loaded = pyqtSignal()

    # 信号：缩放级别改变
    zoom_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._map_widget = parent

    @pyqtSlot(str, str)
    def onIconClick(self, icon_type: str, unit_id: str):
        """
        JavaScript 调用的槽函数：当用户点击地图上的图标时触发

        Args:
            icon_type: 图标类型
            unit_id: 单位ID
        """
        print(f"[MapBridge] 图标点击: type={icon_type}, unit_id={unit_id}")
        self.icon_clicked.emit(icon_type, unit_id)

    @pyqtSlot()
    def onMapLoaded(self):
        """地图加载完成回调"""
        print("[MapBridge] 地图加载完成")
        self.map_loaded.emit()

    @pyqtSlot(int)
    def onZoomChanged(self, zoom: int):
        """缩放级别改变回调"""
        self.zoom_changed.emit(zoom)


class MapWidget(QWidget):
    """
    地图态势展示组件

    使用 QWebEngineView 加载高德地图 HTML 页面，
    通过 QWebChannel 实现 Python 与 JavaScript 的双向通信。

    Usage:
        widget = MapWidget()
        widget.add_icon('warship', 121.5, 31.2, {'name': '辽宁舰', 'unit_id': '001'})
        widget.set_layer_visible('warship', True)
        widget.show()
    """

    # 信号：图标被点击 (icon_type, unit_id)
    iconClicked = pyqtSignal(str, str)

    def __init__(self, parent=None, html_path: Optional[str] = None):
        """
        初始化地图组件

        Args:
            parent: 父组件
            html_path: HTML 文件路径，默认使用内置路径
        """
        super().__init__(parent)

        # 获取 HTML 文件路径
        if html_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(current_dir, 'assets', 'map.html')

        self._html_path = html_path
        self._bridge = MapBridge(self)
        self._is_loaded = False
        self._pending_commands: List[Dict[str, Any]] = []

        self._init_ui()
        self._init_bridge()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建 WebEngineView
        self._web_view = QWebEngineView(self)
        self._web_view.setAttribute(Qt.WA_TranslucentBackground, False)

        # 配置 WebEngine
        settings = self._web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)

        # 加载 HTML
        html_url = f"file://{self._html_path}"
        self._web_view.setUrl(Qt.QUrl.fromLocalFile(Qt.QUrl(html_url).toLocalFile()))

        # 连接加载信号
        self._web_view.page().loadFinished.connect(self._on_load_finished)

        layout.addWidget(self._web_view)

        # 设置最小尺寸
        self.setMinimumSize(800, 600)

    def _init_bridge(self):
        """初始化 QWebChannel 桥接"""
        channel = QWebChannel(self._web_view.page())
        self._web_view.page().setWebChannel(channel)
        channel.registerObject('mapBridge', self._bridge)

        # 连接桥接信号
        self._bridge.icon_clicked.connect(self._on_icon_clicked)
        self._bridge.map_loaded.connect(self._on_map_loaded)

    def _on_load_finished(self, ok: bool):
        """页面加载完成回调"""
        if ok:
            print(f"[MapWidget] HTML 加载成功: {self._html_path}")
            self._is_loaded = True
            self._execute_pending_commands()
        else:
            print(f"[MapWidget] HTML 加载失败: {self._html_path}")

    def _on_icon_clicked(self, icon_type: str, unit_id: str):
        """图标点击事件"""
        print(f"[MapWidget] 转发图标点击: type={icon_type}, unit_id={unit_id}")
        self.iconClicked.emit(icon_type, unit_id)

    def _on_map_loaded(self):
        """地图加载完成"""
        pass

    def _execute_pending_commands(self):
        """执行队列中的待执行命令"""
        for cmd in self._pending_commands:
            self._exec_js(cmd['script'])
        self._pending_commands.clear()

    def _exec_js(self, script: str):
        """执行 JavaScript 代码"""
        if not self._is_loaded:
            self._pending_commands.append({'script': script})
            return

        def callback(result):
            if result is not None:
                print(f"[MapWidget] JS 执行结果: {result}")

        self._web_view.page().runJavaScript(script, callback)

    # ==================== 公开 API ====================

    def add_icon(self, icon_type: str, lng: float, lat: float, data: Dict[str, Any]):
        """
        添加单个图标到地图

        Args:
            icon_type: 图标类型 (warship, submarine, base, airport, ammunition, antiAircraft, militaryAircraft, oilDepot)
            lng: 经度
            lat: 纬度
            data: 附加数据字典
        """
        data_json = json.dumps(data, ensure_ascii=False)
        script = f"""
            if (window.mapAPI && window.mapAPI.addIcon) {{
                window.mapAPI.addIcon('{icon_type}', {lng}, {lat}, {data_json});
            }}
        """
        self._exec_js(script)

    def add_icons_batch(self, icons: List[Dict[str, Any]]):
        """
        批量添加图标

        Args:
            icons: 图标列表，每个元素包含:
                - type: 图标类型
                - lng: 经度
                - lat: 纬度
                - data: 附加数据
        """
        icons_json = json.dumps(icons, ensure_ascii=False)
        script = f"""
            if (window.mapAPI && window.mapAPI.addIconsBatch) {{
                window.mapAPI.addIconsBatch({icons_json});
            }}
        """
        self._exec_js(script)

    def set_layer_visible(self, layer_type: str, visible: bool):
        """
        设置图层可见性

        Args:
            layer_type: 图层类型
            visible: 是否可见
        """
        script = f"""
            if (window.mapAPI && window.mapAPI.setLayerVisible) {{
                window.mapAPI.setLayerVisible('{layer_type}', {str(visible).lower()});
            }}
        """
        self._exec_js(script)

    def add_track(self, points: List[Dict[str, float]], color: str = '#00FFFF', unit_id: str = ''):
        """
        添加航迹线

        Args:
            points: 轨迹点列表 [{lng: float, lat: float}, ...]
            color: 线条颜色
            unit_id: 单位ID
        """
        points_json = json.dumps(points)
        script = f"""
            if (window.mapAPI && window.mapAPI.addTrack) {{
                window.mapAPI.addTrack({points_json}, '{color}', '{unit_id}');
            }}
        """
        self._exec_js(script)

    def add_combat_radius(self, lng: float, lat: float, radius_km: float, color: str = '#FF4444'):
        """
        添加作战半径

        Args:
            lng: 中心经度
            lat: 中心纬度
            radius_km: 半径（公里）
            color: 颜色
        """
        script = f"""
            if (window.mapAPI && window.mapAPI.addCombatRadius) {{
                window.mapAPI.addCombatRadius({lng}, {lat}, {radius_km}, '{color}');
            }}
        """
        self._exec_js(script)

    def add_heatmap(self, data: List[Dict[str, Any]]):
        """
        添加热力图数据

        Args:
            data: 热力数据 [{lng, lat, count}, ...]
        """
        data_json = json.dumps(data)
        script = f"""
            if (window.mapAPI && window.mapAPI.addHeatmap) {{
                window.mapAPI.addHeatmap({data_json});
            }}
        """
        self._exec_js(script)

    def set_heatmap_visible(self, visible: bool):
        """
        设置热力图可见性

        Args:
            visible: 是否可见
        """
        script = f"""
            if (window.mapAPI && window.mapAPI.setHeatmapVisible) {{
                window.mapAPI.setHeatmapVisible({str(visible).lower()});
            }}
        """
        self._exec_js(script)

    def clear_all_icons(self):
        """清除所有图标"""
        script = """
            if (window.mapAPI && window.mapAPI.clearAllIcons) {
                window.mapAPI.clearAllIcons();
            }
        """
        self._exec_js(script)

    def pan_to(self, lng: float, lat: float, zoom: Optional[int] = None):
        """
        移动地图到指定位置

        Args:
            lng: 经度
            lat: 纬度
            zoom: 缩放级别（可选）
        """
        if zoom is not None:
            script = f"""
                if (window.mapAPI && window.mapAPI.panTo) {{
                    window.mapAPI.panTo({lng}, {lat}, {zoom});
                }}
            """
        else:
            script = f"""
                if (window.mapAPI && window.mapAPI.panTo) {{
                    window.mapAPI.panTo({lng}, {lat});
                }}
            """
        self._exec_js(script)

    def run_javascript(self, script: str, callback=None):
        """
        直接执行 JavaScript 代码

        Args:
            script: JavaScript 代码
            callback: 结果回调函数（可选）
        """
        if callback:
            self._web_view.page().runJavaScript(script, callback)
        else:
            self._exec_js(script)

    def is_loaded(self) -> bool:
        """检查地图是否加载完成"""
        return self._is_loaded


# 模块自测
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    widget = MapWidget()

    # 连接信号
    widget.iconClicked.connect(lambda t, uid: print(f"点击: {t}, {uid}"))

    # 模拟添加数据
    def test_add():
        widget.add_icon('warship', 121.5, 31.2, {'name': '测试舰', 'unit_id': '001'})
        widget.add_icons_batch([
            {'type': 'submarine', 'lng': 122.0, 'lat': 30.0, 'data': {'name': '潜艇1'}},
            {'type': 'base', 'lng': 110.0, 'lat': 35.0, 'data': {'name': '基地1'}}
        ])
        widget.set_layer_visible('warship', True)

    # 延迟添加数据，等待页面加载
    QTimer.singleShot(1000, test_add)

    widget.resize(1200, 800)
    widget.show()

    sys.exit(app.exec_())
