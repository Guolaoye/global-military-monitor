"""地图组件 - QWebEngineView地图组件"""
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import os

class MapWidget(QWebEngineView):
    """地图组件（基于 QWebEngineView + 高德/天地图）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_map_html()
    
    def load_map_html(self):
        """加载地图 HTML"""
        html_path = os.path.join(os.path.dirname(__file__), "assets", "map.html")
        if os.path.exists(html_path):
            self.load(QUrl.fromLocalFile(html_path))
        else:
            # 显示占位符
            self.setHtml("<html><body><h1>地图加载中...</h1><p>map.html 未找到</p></body></html>")
    
    def load_amap(self, api_key: str):
        """加载高德地图"""
        # TODO: 实现高德地图 JSAPI 初始化
        pass
    
    def load_tianditu(self, api_key: str):
        """加载天地图"""
        # TODO: 实现天地图初始化
        pass
