"""
Settings Manager - 管理设置持久化到数据库
"""

import sys
import os
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DEFAULT_SETTINGS = {
    # 飞书配置
    'feishu_app_id': {'value': '', 'type': 'str'},
    'feishu_app_secret': {'value': '', 'type': 'str'},
    'feishu_receive_channel_id': {'value': '', 'type': 'str'},
    'feishu_enabled': {'value': 'false', 'type': 'bool'},
    
    # 地图配置
    'map_provider': {'value': 'amap', 'type': 'str'},  # amap/tianditu/osm
    'amap_key': {'value': '', 'type': 'str'},
    'tianditu_key': {'value': '', 'type': 'str'},
    
    # 爬虫配置
    'crawler_enabled': {'value': 'true', 'type': 'bool'},
    'crawler_interval_hours': {'value': '3', 'type': 'int'},
    'crawler_sources': {'value': '{}', 'type': 'json'},
    
    # 预警规则
    'alert_high_threshold': {'value': '7', 'type': 'int'},
    'alert_medium_threshold': {'value': '4', 'type': 'int'},
    'alert_enabled': {'value': 'true', 'type': 'bool'},
    
    # 数据目录
    'obsidian_path': {'value': '', 'type': 'str'},
    'db_path': {'value': '', 'type': 'str'},
    'backup_path': {'value': '', 'type': 'str'},
    
    # AI模型
    'ai_model': {'value': 'minimax', 'type': 'str'},
    'ai_api_key': {'value': '', 'type': 'str'},
    'ai_temperature': {'value': '0.7', 'type': 'float'},
}

class SettingsManager:
    """设置管理器 - 加载/保存设置到SQLite数据库"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, 'data', 'military_monitor.db')
        
        self.db_path = db_path
        self._ensure_db()
        self._ensure_defaults()
    
    def _ensure_db(self):
        """确保数据库和settings表存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT,
                setting_type TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _ensure_defaults(self):
        """确保默认设置存在"""
        for key, cfg in DEFAULT_SETTINGS.items():
            if self.get(key) is None:
                self.save(key, cfg['value'], cfg['type'])
    
    def load(self):
        """加载所有设置"""
        settings = {}
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT setting_key, setting_value, setting_type FROM settings')
        for row in cursor.fetchall():
            key, value, vtype = row
            settings[key] = self._cast_value(value, vtype)
        conn.close()
        
        # 合并.env文件中的设置
        env_settings = self._load_env()
        settings.update(env_settings)
        return settings
    
    def _load_env(self):
        """从.env文件加载设置"""
        env_settings = {}
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(project_root, '.env')
        
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key in DEFAULT_SETTINGS:
                            env_settings[key] = self._cast_value(value, DEFAULT_SETTINGS[key]['type'])
        return env_settings
    
    def save(self, key, value, vtype=None):
        """保存设置到数据库"""
        if vtype is None:
            vtype = DEFAULT_SETTINGS.get(key, {}).get('type', 'str')
        
        value_str = str(value)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (setting_key, setting_value, setting_type)
            VALUES (?, ?, ?)
        ''', (key, value_str, vtype))
        conn.commit()
        conn.close()
        
        # 同时更新.env文件
        self._update_env(key, value_str)
    
    def _update_env(self, key, value):
        """更新.env文件中的设置"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(project_root, '.env')
        
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 查找并更新或添加
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f'{key}='):
                new_lines.append(f'{key}={value}\n')
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f'{key}={value}\n')
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    def get(self, key, default=None):
        """获取设置值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT setting_value, setting_type FROM settings WHERE setting_key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._cast_value(row[0], row[1])
        return default
    
    def reset_to_default(self, key):
        """重置设置到默认值"""
        if key in DEFAULT_SETTINGS:
            cfg = DEFAULT_SETTINGS[key]
            self.save(key, cfg['value'], cfg['type'])
    
    def export_config(self):
        """导出配置为.env文件"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(project_root, '.env')
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('# Global Military Monitor Configuration\n')
            f.write('# 全球军事动态分析研判系统配置\n\n')
            
            for key, cfg in DEFAULT_SETTINGS.items():
                value = self.get(key, cfg['value'])
                f.write(f'{key}={value}\n')
        
        return env_path
    
    def _cast_value(self, value, vtype):
        """根据类型转换值"""
        if vtype == 'int':
            return int(value) if value else 0
        elif vtype == 'float':
            return float(value) if value else 0.0
        elif vtype == 'bool':
            return value.lower() in ('true', '1', 'yes', 'on') if value else False
        elif vtype == 'json':
            import json
            try:
                return json.loads(value)
            except:
                return {}
        return value

# 全局实例
_manager = None

def get_settings_manager():
    """获取全局设置管理器实例"""
    global _manager
    if _manager is None:
        _manager = SettingsManager()
    return _manager
