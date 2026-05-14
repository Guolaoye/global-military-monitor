# 全球军事动态分析研判系统 — 项目规范书 V2.1

> 本文档为项目规范书，是阶段一交付物的一部分。

## 第一章 项目概述

**项目名称：** 全球军事动态分析研判系统
**版本：** V2.1
**编写日期：** 2026-05-14

本系统是一个基于 AI 的军事情报分析平台，通过情报收集引擎自动抓取全球军事动态数据，在地图上可视化呈现军事力量结构和实时态势，支持真实/模拟推演，并可通过飞书机器人推送预警。

## 第二章 系统架构

### 2.1 整体架构

系统采用分层架构，分为数据层、业务逻辑层、表示层三大层：

- **数据层：** PostgreSQL（结构化数据）+ Obsidian（非结构化文本/笔记）
- **业务逻辑层：** Python（情报收集引擎、态势推演引擎）
- **表示层：** PyQt5/Tkinter桌面应用（前端界面）
  - ⚠️ 全中文界面，所有标签、按钮、提示信息均使用中文（配置文件、代码注释除外）
- **通信层：** 飞书机器人API（预警通知）

### 2.2 技术选型

| 类别 | 技术方案 | 选型理由 |
|------|----------|----------|
| 编程语言 | Python 3.10+ | 生态丰富，适合情报爬取+数据处理；跨平台 |
| 桌面框架 | PyQt5 | 功能完整，支持复杂地图UI；成熟稳定 |
| 数据库 | PostgreSQL 15+ | 支持JSON类型、地理信息扩展（PostGIS）、关系查询 |
| 笔记系统 | Obsidian | 双向链接、思维导图、Markdown；适合非结构化情报分析 |
| 地图底图 | 高德地图JSAPI + 天地图（可切换） | 国内免费、稳定；高德成熟易用；天地图为国家队备选 |
| 船舶追踪 | cruisingearth.com API / AIS | 实时全球船舶数据，含军事船只 |
| 版本控制 | Git + GitHub | 多人协作、代码历史、issue管理 |
| 打包发布 | PyInstaller / fbs | Python桌面应用打包成exe，跨平台分发 |

## 第三章 功能模块详细设计

### 3.1 模块一：军事情报收集处理引擎

#### 3.1.1 信息源分类与抓取策略

| 信息类别 | 示例来源 | 抓取频率 | 可信度 |
|----------|----------|----------|--------|
| 官方公告 | 美国国防部官网、俄罗斯国防部官网、日本防卫省官网 | 每小时 | ★★★★★ 最高 |
| AIS船舶追踪 | cruisingearth.com、vesseltracker.com | 每小时 | ★★★★★ 最高 |
| 军事自媒体（10万粉+） | 微博军事大V、微信公众号、B站军事UP主 | 每2小时 | ★★★ 中 |
| 民间数据站 | 各国民间军事爱好者整理的数据网站 | 每4小时 | ★★ 较低 |
| 其他开源情报(OSINT) | GitHub开源军事数据项目、Reddit军事板块 | 每6小时 | ★★ 较低 |

#### 3.1.2 爬虫架构

- **调度器（Scheduler）：** 基于 APScheduler，支持可配置的抓取间隔（默认2小时一次，范围1-6小时）
- **网站适配器（Adapters）：** 每个信息源一个适配器类，统一接口（fetch() → ParseResult）
- **解析器（Parsers）：** 从HTML/JSON中提取情报结构化数据
- **置信度计算器（Confidence Calculator）：** 基于来源类型、多源交叉验证计算置信度
- **写入器（Writers）：** 高可信度直接入库；低可信度入待审批队列
- **去重器（Deduplicator）：** 基于 (unit_id + event_type + timestamp) 去重

#### 3.1.3 置信度算法（初版）

- 官方来源：基础分 1.0
- 粉丝10万+自媒体：基础分 0.7
- 民间数据站：基础分 0.5
- 低粉丝自媒体：基础分 0.3
- 多源交叉验证（≥3个不同来源确认）：+0.2
- 单源独家：-0.1

## 第六章 项目目录结构

See the actual project directory at `./` (项目根目录).

```
global-military-monitor/          ← 项目根目录
├── README.md                     ← 项目说明
├── requirements.txt              ← Python依赖
├── .env.example                  ← 环境变量示例
├── setup_env.sh                  ← 开发环境安装脚本（Linux）
├── setup_env.bat                 ← 开发环境安装脚本（Windows）
├── pyproject.toml                ← 项目配置
├── SPEC.md                       ← 本文档（项目规范书）
├── src/                          ← 源代码
│   ├── __init__.py
│   ├── main.py                   ← 程序入口
│   ├── config.py                 ← 配置加载
│   ├── db/                       ← 数据库层
│   │   ├── __init__.py
│   │   ├── connection.py        ← PostgreSQL连接管理
│   │   ├── models.py             ← ORM模型（SQLAlchemy）
│   │   └── migrations/          ← 数据库迁移脚本
│   ├── crawler/                  ← 情报收集引擎
│   │   ├── __init__.py
│   │   ├── base.py               ← 爬虫基类（适配器模式）
│   │   ├── scheduler.py         ← APScheduler调度器
│   │   ├── confidence.py         ← 置信度计算
│   │   ├── deduplicator.py       ← 去重器
│   │   ├── adapters/            ← 各信息源适配器
│   │   │   ├── __init__.py
│   │   │   ├── ais_cruisingearth.py
│   │   │   ├── us_defense_gov.py
│   │   │   ├── ru_defense_gov.py
│   │   │   ├── jp_mod_go_jp.py
│   │   │   └── wechat自媒体.py
│   │   └── notification.py      ← 飞书通知
│   ├── map/                      ← 地图模块
│   │   ├── __init__.py
│   │   ├── map_widget.py        ← QWebEngineView地图组件
│   │   ├── icon_manager.py       ← 图标管理（聚合/展开）
│   │   ├── overlay.py            ← 叠加层（图标/轨迹/热力图）
│   │   └── assets/              ← 地图资源
│   │       ├── map.html         ← 高德地图初始化HTML
│   │       ├── map.js           ← 地图交互JS
│   │       └── icons/           ← 军事图标素材
│   ├── structure/                ← 军事力量结构模块
│   │   ├── __init__.py
│   │   ├── tree_view.py         ← 树状图视图
│   │   ├── graph_view.py        ← 网状图视图
│   │   └── unit_detail.py       ← 单位详情页
│   ├── analysis/                 ← 态势分析模块
│   │   ├── __init__.py
│   │   ├── real_situation.py    ← 真实态势推演
│   │   ├── sim_situation.py     ← 模拟态势推演
│   │   ├── damage_calc.py       ← 毁伤计算（兵棋引擎）
│   │   └── weather.py           ← 气象数据接入
│   ├── obsidian/                 ← Obsidian同步模块
│   │   ├── __init__.py
│   │   ├── sync.py              ← 同步逻辑
│   │   └── template.py          ← MD模板
│   └── ui/                      ← UI公共组件
│       ├── __init__.py
│       ├── settings.py          ← 设置界面
│       └── widgets.py           ← 通用组件
├── tests/                       ← 测试
│   ├── __init__.py
│   ├── test_crawler.py
│   ├── test_map.py
│   └── test_db.py
├── docs/                        ← 文档
│   ├── 数据库设计文档.md
│   ├── 适配器编写规范.md
│   ├── 安装指引.md
│   └── 用户手册.md
└── outputs/                     ← 运行时输出
    ├── logs/                    ← 日志
    └── cache/                   ← 临时缓存
```

## 第七章 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 部分GitHub参考项目国内无法访问 | 影响调研效率 | 使用GitHub加速源 ghfast.top；备用方案用国内镜像 |
| 高德/天地图API配额不足 | 地图无法加载 | 多底图切换；申请企业认证获取更高配额 |
| cruisingearth.com变更接口 | AIS数据中断 | 多源交叉；备用AIS源 vesseltracker.com |
| 小海关开发环境问题 | 进度延误 | 粪叉子远程协助安装；必要时提供Docker容器方案 |
| 情报可信度判断失误 | 态势误判 | 低可信度强制人工审批；不自动化入库 |

## 第八章 验收标准（V1.0）

- ✅ 情报收集：每小时自动抓取AIS+至少3个官方来源，支持飞书预警推送
- ✅ 地图展示：2D卫星地图加载成功，军事图标叠加显示，支持缩放/聚合/展开
- ✅ 力量结构：树状图/网状图双模式切换，台湾地区示例数据可正常展示
- ✅ 真实态势：时间轴回溯历史轨迹，点击地图显示受影响单位
- ✅ 模拟推演：可复制单位进行参数调整推演，不影响原始数据
- ✅ 设置功能：底图切换、API Key配置、爬虫频率调整均生效
- ✅ 文档齐全：数据库设计文档、安装指引、开发文档均已交付
- ✅ AI情报分析：情报入库后自动触发分析，摘要写入数据库，可信度<0.7情报给出采纳建议
- ✅ AI态势辅助：真实/模拟推演时自动输出文字分析报告，重大前兆识别触发飞书预警
- ✅ AI快速查询：右下角问答入口支持连续对话，查询历史自动存入Obsidian
- ✅ AI模型切换：设置中可切换MiniMax/OpenAI模型，API Key独立配置
