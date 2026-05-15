"""Obsidian 同步逻辑

支持情报入库时同步在 Obsidian Vault 创建/更新 Markdown 文件。
文件命名规则：unit_uuid.md（按规范书要求）
Frontmatter 包含 unit_uuid、created_at、source 等元数据。
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

from .template import ObsidianTemplate


class ObsidianSync:
    """
    Obsidian 同步器
    
    支持同步情报和单位到 Obsidian Vault。
    文件以 unit_uuid 命名，包含 YAML frontmatter。
    """
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.template = ObsidianTemplate()
        self.sync_log: List[Dict] = []
    
    def sync_unit(self, unit_data: Dict) -> bool:
        """
        同步单位到 Obsidian
        
        Args:
            unit_data: 单位数据，应包含：
                - unit_uuid: 单位UUID（文件名）
                - unit_name: 单位名称
                - unit_code: 番号
                - unit_level: 级别
                - country: 国家
                - branch: 军种
                - commander: 指挥官
                - strength: 编制员额
                - location: 驻地
                - source: 数据来源
                - created_at: 创建时间
        
        Returns:
            bool: 是否成功
        """
        try:
            unit_uuid = unit_data.get("unit_uuid")
            if not unit_uuid:
                print("同步失败: unit_uuid 不能为空")
                return False
            
            # 构建文件路径: vault/单位/{国家}/{单位名}_{uuid}.md
            country = unit_data.get("country", "未知")
            unit_name = unit_data.get("unit_name", "未知单位")
            # 替换文件名中的非法字符
            safe_name = "".join(c for c in unit_name if c not in '<>:"/\\|?*')
            
            file_path = self.vault_path / "单位" / country / f"{safe_name}_{unit_uuid[:8]}.md"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建 frontmatter
            frontmatter = self._build_frontmatter(
                uid=unit_uuid,
                entity_type="unit",
                title=unit_name,
                source=unit_data.get("source"),
                created_at=unit_data.get("created_at"),
                tags=unit_data.get("tags", []),
            )
            
            # 构建正文
            content = self.template.unit_template({
                "unit_uuid": unit_uuid,
                "unit_name": unit_name,
                "unit_code": unit_data.get("unit_code"),
                "unit_level": unit_data.get("unit_level"),
                "unit_type": unit_data.get("unit_type"),
                "country": country,
                "branch": unit_data.get("branch"),
                "commander": unit_data.get("commander"),
                "strength": unit_data.get("strength"),
                "location": unit_data.get("location"),
                "is_active": unit_data.get("is_active", True),
            })
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter)
                f.write("\n")
                f.write(content)
            
            self.sync_log.append({
                "time": datetime.now().isoformat(),
                "action": "sync_unit",
                "file": str(file_path),
                "uuid": unit_uuid,
            })
            return True
        
        except Exception as e:
            print(f"Obsidian 单位同步失败: {e}")
            return False
    
    def sync_intelligence(self, intel_data: Dict) -> bool:
        """
        同步情报到 Obsidian
        
        Args:
            intel_data: 情报数据，应包含：
                - intel_uuid: 情报UUID
                - unit_uuid: 关联单位UUID（文件名）
                - title: 标题
                - intel_type: 类型
                - content: 内容
                - source: 来源
                - event_date: 事件时间
        
        Returns:
            bool: 是否成功
        """
        try:
            unit_uuid = intel_data.get("unit_uuid", "unknown")
            title = intel_data.get("title", "无标题")
            intel_uuid = intel_data.get("intel_uuid", str(datetime.now().timestamp()))
            
            # 构建文件路径: vault/情报/{国家}/{unit_uuid}.md
            country = intel_data.get("country", "情报")
            file_name = f"{unit_uuid[:8]}_{intel_uuid[:8]}.md"
            file_path = self.vault_path / "情报" / country / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建 frontmatter
            frontmatter = self._build_frontmatter(
                uid=intel_uuid,
                entity_type="intelligence",
                title=title,
                source=intel_data.get("source"),
                created_at=intel_data.get("event_date"),
                tags=[intel_data.get("intel_type", "unknown")],
            )
            
            # 构建正文
            content = self.template.intel_template({
                "intel_uuid": intel_uuid,
                "intel_type": intel_data.get("intel_type"),
                "confidence": intel_data.get("confidence"),
                "source_url": intel_data.get("source"),
                "event_date": intel_data.get("event_date"),
                "content": intel_data.get("content", ""),
                "related_units": intel_data.get("related_units", ""),
            })
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(frontmatter)
                f.write("\n")
                f.write(content)
            
            self.sync_log.append({
                "time": datetime.now().isoformat(),
                "action": "sync_intel",
                "file": str(file_path),
                "uuid": intel_uuid,
            })
            return True
        
        except Exception as e:
            print(f"Obsidian 情报同步失败: {e}")
            return False
    
    def _build_frontmatter(
        self,
        uid: str,
        entity_type: str,
        title: str,
        source: Optional[str] = None,
        created_at: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        构建 YAML frontmatter
        
        Args:
            uid: 实体UUID
            entity_type: 实体类型（unit / intelligence）
            title: 标题
            source: 来源
            created_at: 创建时间
            tags: 标签列表
        
        Returns:
            str: YAML frontmatter 字符串
        """
        if created_at is None:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if tags is None:
            tags = []
        
        lines = [
            "---",
            f"uid: {uid}",
            f"type: {entity_type}",
            f"title: {title}",
            f"created_at: {created_at}",
        ]
        
        if source:
            lines.append(f"source: {source}")
        
        if tags:
            tags_str = ", ".join(f"'{t}'" if " " in t else t for t in tags)
            lines.append(f"tags: [{tags_str}]")
        
        lines.append("---")
        
        return "\n".join(lines)
    
    def get_sync_status(self) -> List[Dict]:
        """获取同步状态日志"""
        return self.sync_log
    
    def get_sync_stats(self) -> Dict:
        """获取同步统计"""
        stats = {"total": len(self.sync_log), "units": 0, "intel": 0}
        for entry in self.sync_log:
            if entry["action"] == "sync_unit":
                stats["units"] += 1
            elif entry["action"] == "sync_intel":
                stats["intel"] += 1
        return stats
    
    def clear_log(self):
        """清空同步日志"""
        self.sync_log = []