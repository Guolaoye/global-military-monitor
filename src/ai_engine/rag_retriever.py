"""RAG 检索器"""
import sys
import os
import json
import re
from typing import List, Dict, Tuple
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.db.connection import get_cursor


class RAGRetriever:
    """RAG 检索器 — PostgreSQL + Obsidian → 向量检索 → LLM"""

    def __init__(self, db_path: str = None, obsidian_path: str = None):
        self.db_path = db_path
        self.obsidian_path = obsidian_path or os.path.expanduser("~/Documents/军事知识库")
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            from src.config import load_config
            config = load_config()
            self.obsidian_path = config.get("OBSIDIAN_PATH", self.obsidian_path)
        except Exception:
            pass

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            List[dict]: 相关文档列表 [{"source": "db"|"obsidian", "content": "...", "score": float}]
        """
        results = []

        # 1. 从 PostgreSQL 检索
        db_results = self._retrieve_from_db(query, top_k)
        results.extend(db_results)

        # 2. 从 Obsidian 检索
        obsidian_results = self._retrieve_from_obsidian(query, top_k)
        results.extend(obsidian_results)

        # 3. 排序并返回 top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _retrieve_from_db(self, query: str, top_k: int) -> List[Dict]:
        """从数据库检索情报"""
        results = []
        try:
            with get_cursor() as cur:
                # 简单的文本匹配检索
                cur.execute(
                    """
                    SELECT intel_id, title, content, intel_type, country, event_date, credibility
                    FROM intelligence
                    WHERE title LIKE %s OR content LIKE %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (f"%{query}%", f"%{query}%", top_k)
                )
                rows = cur.fetchall()

            for row in rows:
                results.append({
                    "source": "db",
                    "type": "intelligence",
                    "intel_id": str(row[0]),
                    "title": row[1],
                    "content": row[2],
                    "intel_type": row[3],
                    "country": row[4],
                    "event_date": str(row[5]) if row[5] else "",
                    "score": self._calculate_similarity(query, row[1] + " " + (row[2] or "")),
                })
        except Exception as e:
            print(f"DB检索失败: {e}")

        return results

    def _retrieve_from_obsidian(self, query: str, top_k: int) -> List[Dict]:
        """从 Obsidian 检索"""
        results = []
        obsidian_path = Path(self.obsidian_path)

        if not obsidian_path.exists():
            return results

        # 搜索所有 markdown 文件
        try:
            for md_file in obsidian_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    # 简单文本匹配
                    if query in content or query in md_file.name:
                        score = self._calculate_similarity(query, content[:500] + md_file.name)
                        results.append({
                            "source": "obsidian",
                            "type": "note",
                            "file_path": str(md_file),
                            "title": md_file.stem,
                            "content": content[:1000],
                            "score": score,
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"Obsidian检索失败: {e}")

        # 按分数排序并返回 top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _calculate_similarity(self, query: str, text: str) -> float:
        """简单的文本相似度计算（词重叠率）"""
        if not text:
            return 0.0
        query_words = set(re.findall(r'[\w]+', query.lower()))
        text_words = set(re.findall(r'[\w]+', text.lower()))
        if not query_words:
            return 0.0
        intersection = query_words & text_words
        union = query_words | text_words
        return len(intersection) / len(union) if union else 0.0

    def build_context(self, query: str) -> str:
        """构建 RAG 上下文"""
        results = self.retrieve(query, top_k=5)
        if not results:
            return "未找到相关背景信息。"
        context_parts = ["【相关背景资料】"]
        for i, r in enumerate(results, 1):
            source = "情报库" if r["source"] == "db" else "知识库"
            context_parts.append(f"--- 来源{i} ({source}) ---")
            context_parts.append(f"标题: {r.get('title', r.get('file_path', '未知'))}")
            content = r.get('content', '')[:500]
            context_parts.append(f"内容: {content}")
            context_parts.append("")
        return "\n".join(context_parts)

    def index_intelligence(self, intel_data: dict):
        """将情报添加到检索索引"""
        try:
            with get_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO intelligence (intel_id, title, content, intel_type, country, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (intel_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content
                    """,
                    (
                        intel_data.get("intel_id"),
                        intel_data.get("title", ""),
                        intel_data.get("content", ""),
                        intel_data.get("intel_type", "unknown"),
                        intel_data.get("country", "未知"),
                        intel_data.get("created_at"),
                    )
                )
        except Exception as e:
            print(f"索引情报失败: {e}")
