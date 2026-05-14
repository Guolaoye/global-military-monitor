#!/bin/bash
# 全球军事动态分析研判系统 - 环境安装脚本
# 运行方式: bash setup_env.sh

set -e

echo "=== 环境安装脚本 ==="

# 检查 Python 版本
python3 --version || { echo "错误: Python 3 未安装"; exit 1; }

# 安装系统依赖 (需要 sudo)
if command -v apt-get &> /dev/null; then
    echo "[1/5] 安装系统依赖..."
    sudo apt-get update
    sudo apt-get install -y postgresql-16 postgresql-client-16 python3-pip git
fi

# 启动 PostgreSQL
echo "[2/5] 启动 PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
echo "[3/5] 初始化数据库..."
sudo -u postgres psql -c "CREATE USER guo WITH PASSWORD 'gxy11999966' CREATEDB;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE global_military_monitor OWNER guo;" 2>/dev/null || true

# 运行数据库迁移
echo "[4/5] 运行数据库迁移..."
PGPASSWORD=gxy11999966 psql -U guo -d global_military_monitor -f src/db/migrations/001_initial_schema.sql

# 安装 Python 依赖
echo "[5/5] 安装 Python 依赖..."
pip3 install --break-system-packages -r requirements.txt

echo "=== 环境安装完成 ==="
echo "数据库: global_military_monitor"
echo "用户: guo / gxy11999966"
