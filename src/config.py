"""配置加载模块"""
import os
from pathlib import Path

def load_config():
    """从环境变量或 .env 文件加载配置"""
    config = {}
    env_file = Path(__file__).parent.parent / ".env"
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    # 数据库配置
    config["DB_HOST"] = os.environ.get("DB_HOST", "localhost")
    config["DB_PORT"] = int(os.environ.get("DB_PORT", "5432"))
    config["DB_NAME"] = os.environ.get("DB_NAME", "global_military_monitor")
    config["DB_USER"] = os.environ.get("DB_USER", "postgres")
    config["DB_PASSWORD"] = os.environ.get("DB_PASSWORD", "")
    
    # 高德地图 API
    config["AMAP_API_KEY"] = os.environ.get("AMAP_API_KEY", "")
    
    # 飞书配置
    config["FEISHU_APP_ID"] = os.environ.get("FEISHU_APP_ID", "")
    config["FEISHU_APP_SECRET"] = os.environ.get("FEISHU_APP_SECRET", "")
    
    # AI 模型
    config["AI_MODEL"] = os.environ.get("AI_MODEL", "mini-max")
    config["AI_API_KEY"] = os.environ.get("AI_API_KEY", "")
    
    # 爬虫配置
    config["CRAWLER_INTERVAL_HOURS"] = int(os.environ.get("CRAWLER_INTERVAL_HOURS", "2"))
    
    return config
