"""通用 UI 组件"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QDialog, QTextEdit)
from PyQt5.QtCore import Qt

class StatusBar(QWidget):
    """状态栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.db_status = QLabel("数据库: 未连接")
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.db_status)
        self.setLayout(layout)
    
    def set_status(self, text: str):
        self.status_label.setText(text)
    
    def set_db_status(self, connected: bool):
        self.db_status.setText(f"数据库: {'✅ 已连接' if connected else '❌ 未连接'}")

class UnitInfoPanel(QWidget):
    """单位信息面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.name_label = QLabel("未选择单位")
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        layout.addWidget(self.name_label)
        layout.addWidget(self.detail_text)
        self.setLayout(layout)
    
    def show_unit(self, unit_data: dict):
        self.name_label.setText(unit_data.get("name", "未知单位"))
        self.detail_text.setPlainText(str(unit_data))
    
    def clear(self):
        self.name_label.setText("未选择单位")
        self.detail_text.clear()
