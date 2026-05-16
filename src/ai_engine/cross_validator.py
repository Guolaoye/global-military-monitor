"""多源情报交叉验证"""
import sys
import os
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.db.connection import get_cursor


class CrossValidator:
    """多源情报交叉验证器"""

    def __init__(self):
        self.contradiction_threshold = 0.3  # 矛盾阈值

    def validate(self, intel_list: List[dict]) -> dict:
        """
        验证一组情报的一致性

        Returns:
            dict: {
                "is_consistent": bool,
                "credibility_score": float,
                "contradictions": List[str],
                "verification_notes": str,
            }
        """
        if not intel_list:
            return {
                "is_consistent": True,
                "credibility_score": 0.0,
                "contradictions": [],
                "verification_notes": "无情报可供验证",
            }

        # 检查矛盾
        contradictions = self.find_contradictions(intel_list)

        # 计算综合置信度
        credibility_score = self.calculate_credibility(intel_list)

        # 生成验证备注
        notes = self._generate_notes(intel_list, contradictions, credibility_score)

        return {
            "is_consistent": len(contradictions) == 0,
            "credibility_score": credibility_score,
            "contradictions": contradictions,
            "verification_notes": notes,
        }

    def find_contradictions(self, intel_list: List[dict]) -> List[str]:
        """查找矛盾的情报报告"""
        contradictions = []
        n = len(intel_list)

        for i in range(n):
            for j in range(i + 1, n):
                conflict = self._check_pair_contradiction(intel_list[i], intel_list[j])
                if conflict:
                    contradictions.append(conflict)

        return contradictions

    def _check_pair_contradiction(self, intel_a: dict, intel_b: dict) -> str:
        """检查两条情报是否矛盾"""
        # 同一事件，时间接近，结论相反 -> 矛盾
        if intel_a.get("intel_type") != intel_b.get("intel_type"):
            return None

        # 检查时间接近性
        date_a = intel_a.get("event_date", "")
        date_b = intel_b.get("event_date", "")
        # 简化：直接用字符串比较
        if date_a != date_b:
            # 如果时间不同，跳过（可能是不同事件）
            return None

        # 检查地点
        location_a = self._extract_location(intel_a)
        location_b = self._extract_location(intel_b)
        if location_a and location_b and location_a != location_b:
            return f"地点矛盾：'{location_a}' vs '{location_b}'"

        # 检查行动方向矛盾
        direction_a = self._extract_direction(intel_a)
        direction_b = self._extract_direction(intel_b)
        if direction_a and direction_b and direction_a != direction_b:
            return f"方向矛盾：'{direction_a}' vs '{direction_b}'"

        return None

    def _extract_location(self, intel: dict) -> str:
        """提取情报中的位置信息"""
        from src.ai_engine.entity_extractor import EntityExtractor
        extractor = EntityExtractor()
        text = f"{intel.get('title', '')} {intel.get('content', '')}"
        entities = extractor.extract(text)
        locations = [e["text"] for e in entities if e["type"] == "location"]
        return ";".join(locations[:2]) if locations else ""

    def _extract_direction(self, intel: dict) -> str:
        """提取行动方向（进攻/撤退等）"""
        text = f"{intel.get('title', '')} {intel.get('content', '')}"
        # 简化：检测关键词
        if any(k in text for k in ["进攻", "入侵", "发起", "攻击"]):
            return "进攻"
        if any(k in text for k in ["撤退", "撤离", "后撤", "收缩"]):
            return "撤退"
        if any(k in text for k in ["演习", "演练", "训练"]):
            return "演习"
        if any(k in text for k in ["部署", "进驻", "增援"]):
            return "部署"
        return ""

    def calculate_credibility(self, intel_list: List[dict]) -> float:
        """
        计算情报综合置信度

        规则：
        - 多源确认：+0.2
        - 来源权威性加成
        - 矛盾惩罚
        """
        if not intel_list:
            return 0.0

        # 基础置信度
        base_score = 0.5

        # 来源可靠性加成
        reliability_scores = {
            "A": 0.9, "B": 0.75, "C": 0.5, "D": 0.3,
        }
        reliability_bonus = sum(
            reliability_scores.get(i.get("source_reliability", "C"), 0.5)
            for i in intel_list
        ) / len(intel_list)

        # 多源确认加成（≥3个来源确认同一事件）
        if len(intel_list) >= 3:
            base_score += 0.15

        # 矛盾惩罚
        contradictions = self.find_contradictions(intel_list)
        penalty = len(contradictions) * 0.1

        credibility = base_score * 0.3 + reliability_bonus * 0.7 - penalty
        return max(0.0, min(1.0, credibility))

    def suggest_approval(self, intel: dict) -> str:
        """
        对低置信度情报给出采纳建议

        Args:
            intel: 单条情报

        Returns:
            str: 采纳建议
        """
        confidence = self._calculate_single_confidence(intel)

        if confidence >= 0.8:
            return "建议采纳入库"
        elif confidence >= 0.7:
            return "建议采纳，但需持续关注后续情报"
        elif confidence >= 0.5:
            return "建议暂存，待多源验证后再决定"
        else:
            return "建议搁置，置信度过低"

    def _calculate_single_confidence(self, intel: dict) -> float:
        """计算单条情报置信度"""
        base = 0.5
        reliability_map = {"A": 0.9, "B": 0.75, "C": 0.5, "D": 0.3}
        base = reliability_map.get(intel.get("source_reliability", "C"), 0.5)
        return max(0.0, min(1.0, base))
