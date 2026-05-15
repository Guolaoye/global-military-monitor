"""Obsidian Markdown 模板

提供 Obsidian Markdown 文件模板，支持 frontmatter 元数据。
"""
from typing import Dict, List, Optional
from datetime import datetime


class ObsidianTemplate:
    """
    Obsidian Markdown 模板
    
    生成的 Markdown 格式：
    - 包含 YAML frontmatter（unit_uuid、created_at、source 等元数据）
    - 正文使用标准 Markdown 格式
    """
    
    @staticmethod
    def unit_template(unit_data: Dict) -> str:
        """
        单位 Markdown 模板
        
        Args:
            unit_data: 单位数据字典
        
        Returns:
            str: Markdown 格式的字符串
        """
        unit_uuid = unit_data.get("unit_uuid", "N/A")
        unit_name = unit_data.get("unit_name", unit_data.get("name_cn", "未知单位"))
        unit_code = unit_data.get("unit_code", "N/A")
        unit_level = unit_data.get("unit_level", "N/A")
        unit_type = unit_data.get("unit_type", "N/A")
        is_active = unit_data.get("is_active", True)
        
        country = unit_data.get("country", "N/A")
        branch = unit_data.get("branch", "N/A")
        parent_unit = unit_data.get("parent_unit", "N/A")
        
        commander = unit_data.get("commander", "未知")
        strength = unit_data.get("strength", "未知")
        
        location = unit_data.get("location", {})
        if isinstance(location, dict):
            loc_name = location.get("name", "未知")
            lat = location.get("latitude", "N/A")
            lng = location.get("longitude", "N/A")
        else:
            loc_name = str(location) if location else "未知"
            lat = lng = "N/A"
        
        status_icon = "✅ 活跃" if is_active else "❌ 非活跃"
        updated = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return f"""# {unit_name}

## 基本信息

| 字段 | 内容 |
|------|------|
| **UUID** | `{unit_uuid}` |
| **番号** | {unit_code} |
| **级别** | {unit_level} |
| **类型** | {unit_type} |
| **状态** | {status_icon} |

## 所属关系

| 字段 | 内容 |
|------|------|
| **国家/地区** | {country} |
| **军种** | {branch} |
| **上级单位** | {parent_unit} |

## 编制信息

| 字段 | 内容 |
|------|------|
| **指挥官** | {commander} |
| **编制员额** | {strength} 人 |

## 驻地

| 字段 | 内容 |
|------|------|
| **地名** | {loc_name} |
| **纬度** | {lat} |
| **经度** | {lng} |

## 关联情报

> 暂无情报记录

## 预警记录

> 暂无预警

## 备注

-

---

*最后更新：{updated}*
"""
    
    @staticmethod
    def intel_template(intel_data: Dict) -> str:
        """
        情报 Markdown 模板
        
        Args:
            intel_data: 情报数据字典
        
        Returns:
            str: Markdown 格式的字符串
        """
        intel_uuid = intel_data.get("intel_uuid", "N/A")
        title = intel_data.get("title", "情报")
        intel_type = intel_data.get("intel_type", "unknown")
        confidence = intel_data.get("confidence", "N/A")
        source_url = intel_data.get("source_url", intel_data.get("source", "未知"))
        event_date = intel_data.get("event_date", "未知")
        content = intel_data.get("content", "无内容")
        related_units = intel_data.get("related_units", "")
        
        intel_type_map = {
            "movement": "兵力机动",
            "exercise": "军事演习",
            "deployment": "兵力部署",
            "incident": "突发事件",
        }
        intel_type_cn = intel_type_map.get(intel_type, intel_type)
        
        updated = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        related_units_block = f"\n## 关联单位\n\n{related_units}\n" if related_units else ""
        
        return f"""# {title}

## 元数据

| 字段 | 内容 |
|------|------|
| **UUID** | `{intel_uuid}` |
| **类型** | {intel_type_cn} |
| **可信度** | {confidence} |
| **来源** | {source_url} |
| **事件时间** | {event_date} |

## 内容

{content}
{related_units_block}
---

*最后更新：{updated}*
"""
    
    @staticmethod
    def alert_template(alert_data: Dict) -> str:
        """
        预警 Markdown 模板
        """
        alert_uuid = alert_data.get("alert_id", "N/A")
        title = alert_data.get("title", "预警")
        alert_level = alert_data.get("alert_level", "unknown")
        alert_type = alert_data.get("alert_type", "unknown")
        description = alert_data.get("description", "无描述")
        affected_area = alert_data.get("affected_area", "未知")
        start_time = alert_data.get("start_time", "未知")
        end_time = alert_data.get("end_time", "持续中")
        is_active = alert_data.get("is_active", True)
        
        level_map = {
            "red": "🔴 红色",
            "orange": "🟠 橙色",
            "yellow": "🟡 黄色",
            "blue": "🔵 蓝色",
        }
        level_cn = level_map.get(alert_level, alert_level)
        
        status_cn = "⚠️ 活跃" if is_active else "✅ 已解除"
        updated = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return f"""# {title}

## 预警信息

| 字段 | 内容 |
|------|------|
| **UUID** | `{alert_uuid}` |
| **预警等级** | {level_cn} |
| **预警类型** | {alert_type} |
| **状态** | {status_cn} |
| **影响区域** | {affected_area} |
| **开始时间** | {start_time} |
| **解除时间** | {end_time} |

## 描述

{description}

---

*最后更新：{updated}*
"""
