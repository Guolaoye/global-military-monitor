"""程序入口"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """主函数 - 启动应用程序"""
    print("全球军事动态分析研判系统 V1.0")
    print("=" * 40)
    print("配置加载中...")
    
    try:
        from src.config import load_config
        config = load_config()
        print(f"数据库: {config.get('DB_HOST', 'localhost')}:{config.get('DB_PORT', 5432)}/{config.get('DB_NAME', 'global_military_monitor')}")
        print("配置加载成功")
    except Exception as e:
        print(f"配置加载失败: {e}")
        print("使用默认配置启动")
    
    print("\n提示: GUI 模块正在开发中，请耐心等待...")
    
if __name__ == "__main__":
    main()
