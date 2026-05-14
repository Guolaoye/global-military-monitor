"""Obsidian 同步逻辑"""
from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime

class ObsidianSync:
    """Obsidian 同步器"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.sync_log = []
    
    def sync_intelligence(self, intel_data: Dict) -> bool:
        """
        同步情报到 Obsidian
        
        Args:
            intel_data: 情报数据，包含 unit_uuid, title, content 等字段
        Returns:
            bool: 是否成功
        """
        try:
            unit_uuid = intel_data.get("unit_uuid", "unknown")
            title = intel_data.get("title", "无标题")
            
            # 构建文件路径
            country = intel_data.get("country", "未知")
            file_path = self.vault_path / "按国家" / country / "情报" / f"{unit_uuid}.md"
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入 Markdown
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(f"**UUID:** {unit_uuid}\n")
                f.write(f"**类型:** {intel_data.get('intel_type', 'unknown')}\n")
                f.write(f"**时间:** {intel_data.get('event_date', datetime.now())}\n")
                f.write(f"**内容:** {intel_data.get('content', '')}\n")
            
            self.sync_log.append({"time": datetime.now(), "action": "sync", "file": str(file_path)})
            return True
        except Exception as e:
            print(f"Obsidian 同步失败: {e}")
            return False
    
    def get_sync_status(self) -> List[Dict]:
        """获取同步状态"""
        return self.sync_log
