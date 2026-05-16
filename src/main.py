# -*- coding: utf-8 -*-
"""全球军事动态分析研判系统 - 主入口"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

USAGE = """
全球军事动态分析研判系统 V1.0
===============================

用法: python3 src/main.py [模式]

模式:
  web     启动 Web 服务（浏览器访问，推荐）
  gui     启动 PyQt5 GUI 桌面界面
  status  检查系统状态

示例:
  python3 src/main.py web     # 启动 Web 服务
  python3 src/main.py status  # 检查状态

Web 访问地址:
  本机: http://localhost:5000
  局域网: http://<Pi的IP>:5000
"""

def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return
    
    mode = sys.argv[1].lower()
    
    if mode == 'web':
        from src.web_server import app, create_template_folders
        create_template_folders()
        print("=" * 50)
        print("全球军事动态分析研判系统 Web 服务")
        print("=" * 50)
        print("访问地址: http://localhost:5000")
        print("局域网访问: http://<Pi的IP>:5000")
        print("按 Ctrl+C 停止服务")
        print("=" * 50)
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    elif mode == 'gui':
        try:
            from PyQt5.QtWidgets import QApplication
            from src.situational_real.view import RealSituationView
            app = QApplication(sys.argv)
            window = RealSituationView()
            window.setWindowTitle('全球军事动态分析研判系统')
            window.resize(1280, 800)
            window.show()
            sys.exit(app.exec_())
        except ImportError as e:
            print(f"PyQt5 未安装或显示环境不可用: {e}")
            print("建议使用 web 模式: python3 src/main.py web")
            
    elif mode == 'status':
        print("检查系统状态...")
        try:
            from src.db.connection import get_cursor
            with get_cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM military_units')
                count = cur.fetchone()[0]
            print(f"✓ 数据库连接正常，{count} 个单位")
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
        
        try:
            from src.settings.manager import SettingsManager
            mgr = SettingsManager()
            settings = mgr.get_all()
            print(f"✓ 设置模块正常")
        except Exception as e:
            print(f"✗ 设置模块失败: {e}")
            
    else:
        print(f"未知模式: {mode}")
        print(USAGE)

if __name__ == '__main__':
    main()
