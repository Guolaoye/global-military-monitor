"""设置界面"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTabWidget, QComboBox)
from PyQt5.QtCore import pyqtSignal

class SettingsWidget(QWidget):
    """设置界面组件"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 数据库设置
        db_group = QWidget()
        db_layout = QVBoxLayout()
        db_layout.addWidget(QLabel("数据库配置"))
        self.db_host = QLineEdit("localhost")
        self.db_port = QLineEdit("5432")
        db_layout.addWidget(QLabel("主机:"))
        db_layout.addWidget(self.db_host)
        db_layout.addWidget(QLabel("端口:"))
        db_layout.addWidget(self.db_port)
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # API 设置
        api_group = QWidget()
        api_layout = QVBoxLayout()
        api_layout.addWidget(QLabel("API 配置"))
        self.amap_key = QLineEdit()
        self.amap_key.setPlaceholderText("高德地图 API Key")
        api_layout.addWidget(self.amap_key)
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
    
    def save_settings(self):
        """保存设置"""
        settings = {
            "DB_HOST": self.db_host.text(),
            "DB_PORT": self.db_port.text(),
            "AMAP_API_KEY": self.amap_key.text(),
        }
        self.settings_changed.emit(settings)
    
    def load_settings(self, settings: dict):
        """加载设置"""
        self.db_host.setText(settings.get("DB_HOST", "localhost"))
        self.db_port.setText(str(settings.get("DB_PORT", "5432")))
        self.amap_key.setText(settings.get("AMAP_API_KEY", ""))
