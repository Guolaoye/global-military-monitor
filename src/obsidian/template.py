"""Markdown 模板"""
from typing import Dict
from datetime import datetime

class ObsidianTemplate:
    """Obsidian Markdown 模板"""
    
    @staticmethod
    def unit_template(unit_data: Dict) -> str:
        """单位模板"""
        return f"""# {unit_data.get('name_cn', unit_data.get('unit_name', '未知单位'))}

## 基本信息
- **UUID:** {unit_data.get('unit_uuid', 'N/A')}
- **编号:** {unit_data.get('unit_code', 'N/A')}
- **类型:** {unit_data.get('unit_type', 'N/A')}
- **级别:** {unit_data.get('unit_level', 'N/A')}
- **状态:** {'✅ 活跃' if unit_data.get('is_active', True) else '❌ 非活跃'}

## 所属关系
- **国家:** {unit_data.get('country', 'N/A')}
- **军种:** {unit_data.get('branch', 'N/A')}
- **上级单位:** {unit_data.get('parent_unit', 'N/A')}

## 位置
- **纬度:** {unit_data.get('latitude', 'N/A')}
- **经度:** {unit_data.get('longitude', 'N/A')}
- **更新时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 备注
{unit_data.get('notes', '')}
"""
    
    @staticmethod
    def intel_template(intel_data: Dict) -> str:
        """情报模板"""
        return f"""# {intel_data.get('title', '情报')}

## 元数据
- **UUID:** {intel_data.get('intel_uuid', 'N/A')}
- **类型:** {intel_data.get('intel_type', 'N/A')}
- **可信度:** {intel_data.get('confidence', 'N/A')}
- **来源:** {intel_data.get('source_url', 'N/A')}
- **事件时间:** {intel_data.get('event_date', 'N/A')}

## 内容
{intel_data.get('content', '')}

## 关联单位
{intel_data.get('related_units', '')}
"""
