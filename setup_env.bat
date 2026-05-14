@echo off
REM 全球军事动态分析研判系统 - 环境安装脚本（Windows）

echo 安装 Python 依赖...
pip install -r requirements.txt

echo 安装 PostgreSQL...
REM 请从 https://www.postgresql.org/download/ 下载安装 PostgreSQL 16

echo 初始化数据库...
psql -U postgres -c "CREATE DATABASE global_military_monitor;"
psql -U postgres -d global_military_monitor -f src\db\migrations\001_initial_schema.sql

echo 环境安装完成！
pause
