# 全球军事动态分析研判系统

基于 AI 的军事情报分析平台，支持情报自动收集、地图可视化、态势推演和飞书预警。

## 技术栈

- Python 3.10+ / PyQt5
- PostgreSQL 15+ / Obsidian
- 高德地图JSAPI + 天地图

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt --user --break-system-packages

# 初始化数据库
psql -U postgres -d global_military_monitor -f src/db/migrations/001_initial_schema.sql

# 启动应用
python src/main.py
```

## 项目结构

详见 [SPEC.md](SPEC.md)。
