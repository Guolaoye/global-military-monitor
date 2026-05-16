import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def build_alert_card(
    level: str,
    title: str,
    desc: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    timestamp: Optional[str] = None
) -> dict:
    """
    构建飞书告警卡片
    
    Args:
        level: 告警级别 (紧急/高/中/低)
        title: 告警标题
        desc: 告警描述
        lat: 纬度
        lng: 经度
        timestamp: 时间戳
    
    Returns:
        飞书卡片元素数组
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 颜色映射
    color_map = {
        "紧急": "red",
        "高": "orange", 
        "中": "yellow",
        "低": "blue"
    }
    color = color_map.get(level, "grey")
    
    # 构建地图链接
    map_url = ""
    if lat is not None and lng is not None:
        map_url = f"https://www.google.com/maps?q={lat},{lng}"
    
    # 基础卡片元素
    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**【{level}】{title}"
            }
        },
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": desc
            }
        },
        {
            "tag": "hr"
        },
        {
            "tag": "div",
            "fields": [
                {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": f"**时间**\n{timestamp}"
                    }
                }
            ]
        }
    ]
    
    # 添加地图链接
    if map_url:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"[查看位置]({map_url})"
            }
        })
    
    # 构建完整卡片
    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"🚨 军事动态告警 - {level}"
            },
            "template": color
        },
        "elements": elements
    }
    
    return card


def build_alert_message(level: str, title: str, desc: str) -> str:
    """
    构建简单的文本告警消息（用于webhook）
    """
    emoji_map = {
        "紧急": "🔴",
        "高": "🟠",
        "中": "🟡",
        "低": "🔵"
    }
    emoji = emoji_map.get(level, "⚪")
    return f"{emoji} 【{level}】{title}\n\n{desc}\n\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
