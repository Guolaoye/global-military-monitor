import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QSlider, QCheckBox, QGroupBox, QPushButton
    from PyQt5.QtCore import Qt
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False

from .manager import get_settings_manager

class CrawlerConfigWidget(QWidget):
    SOURCES = [
        {'id': 'baidu', 'name': '百度新闻', 'url': 'https://news.baidu.com'},
        {'id': 'sina', 'name': '新浪军事', 'url': 'https://mil.news.sina.com.cn'},
        {'id': '163', 'name': '网易军事', 'url': 'https://war.163.com'},
        {'id': 'xiangshan', 'name': '铁血社区', 'url': 'https://www.tiexue.net'},
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_mgr = get_settings_manager()
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 启用开关
        self.enabled_checkbox = QCheckBox('启用数据爬取')
        layout.addWidget(self.enabled_checkbox)
        
        # 频率设置
        freq_group = QGroupBox('更新频率设置')
        freq_layout = QVBoxLayout()
        
        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setMinimum(1)
        self.interval_slider.setMaximum(6)
        self.interval_slider.setTickPosition(QSlider.TicksBelow)
        self.interval_slider.setTickInterval(1)
        self.interval_slider.valueChanged.connect(self._on_interval_changed)
        freq_layout.addWidget(self.interval_slider)
        
        self.interval_label = QLabel('当前: 3 小时')
        self.interval_label.setAlignment(Qt.AlignCenter)
        freq_layout.addWidget(self.interval_label)
        
        freq_desc = QLabel('建议设置3-6小时，过频繁可能触发反爬')
        freq_desc.setStyleSheet('color: #888; font-size: 11px;')
        freq_layout.addWidget(freq_desc)
        
        freq_group.setLayout(freq_layout)
        layout.addWidget(freq_group)
        
        # 数据源设置
        sources_group = QGroupBox('数据来源设置')
        sources_layout = QVBoxLayout()
        
        self.source_checks = {}
        for source in self.SOURCES:
            checkbox = QCheckBox(f'{source["name"]} ({source["url"]})')
            checkbox.source_id = source['id']
            self.source_checks[source['id']] = checkbox
            sources_layout.addWidget(checkbox)
        
        sources_group.setLayout(sources_layout)
        layout.addWidget(sources_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton('保存配置')
        self.btn_save.clicked.connect(self.save_config)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_reset = QPushButton('重置')
        self.btn_reset.clicked.connect(self.reset_config)
        btn_layout.addWidget(self.btn_reset)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #0078d4;')
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _on_interval_changed(self, value):
        self.interval_label.setText(f'当前: {value} 小时')
    
    def load_config(self):
        self.enabled_checkbox.setChecked(self.settings_mgr.get('crawler_enabled', True))
        self.interval_slider.setValue(int(self.settings_mgr.get('crawler_interval_hours', 3)))
        
        sources = self.settings_mgr.get('crawler_sources', {})
        for source_id, checkbox in self.source_checks.items():
            checkbox.setChecked(sources.get(source_id, True))
    
    def save_config(self):
        self.settings_mgr.save('crawler_enabled', self.enabled_checkbox.isChecked())
        self.settings_mgr.save('crawler_interval_hours', self.interval_slider.value())
        
        sources = {source_id: checkbox.isChecked() for source_id, checkbox in self.source_checks.items()}
        self.settings_mgr.save('crawler_sources', sources)
        
        self.status_label.setText('配置已保存')
        self.status_label.setStyleSheet('color: green;')
    
    def reset_config(self):
        self.settings_mgr.reset_to_default('crawler_enabled')
        self.settings_mgr.reset_to_default('crawler_interval_hours')
        self.settings_mgr.reset_to_default('crawler_sources')
        self.load_config()
        self.status_label.setText('已重置为默认值')
        self.status_label.setStyleSheet('color: orange;')
    
    def get_config(self):
        return {
            'enabled': self.enabled_checkbox.isChecked(),
            'interval_hours': self.interval_slider.value(),
            'sources': {source_id: checkbox.isChecked() for source_id, checkbox in self.source_checks.items()}
        }
