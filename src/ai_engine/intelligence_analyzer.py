"""情报自动分析"""
import sys
import os
import json
import re
from datetime import datetime

# 项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.db.connection import get_cursor
from src.ai_engine.entity_extractor import EntityExtractor
from src.ai_engine.cross_validator import CrossValidator


class IntelligenceAnalyzer:
    """情报自动分析器"""

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.cross_validator = CrossValidator()
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            from src.config import load_config
            self.config = load_config()
        except Exception:
            self.config = {}

    def analyze_intelligence(self, intel_data: dict) -> dict:
        """
        分析单条情报

        Args:
            intel_data: 情报数据字典，包含 title, content, intel_type, event_date 等

        Returns:
            dict: 分析结果，包含 entities, summary, is_abnormal, is_warning, confidence, recommendation
        """
        result = {
            "intel_id": intel_data.get("intel_id", ""),
            "entities": [],
            "summary": "",
            "is_abnormal": False,
            "is_warning": False,
            "confidence": 0.5,
            "recommendation": "",
            "analyzed_at": datetime.now().isoformat(),
        }

        # 1. 实体提取
        text = f"{intel_data.get('title', '')} {intel_data.get('content', '')}"
        entities = self.entity_extractor.extract(text)
        result["entities"] = entities

        # 2. 生成摘要（基于规则，非AI）
        result["summary"] = self._generate_summary(intel_data, entities)

        # 3. 判断是否异常
        result["is_abnormal"] = self._check_abnormal(text, intel_data)

        # 4. 判断是否预警
        result["is_warning"] = self._check_warning(text, intel_data)

        # 5. 计算置信度
        result["confidence"] = self._calculate_confidence(intel_data, entities)

        # 6. 给出采纳建议
        result["recommendation"] = self._generate_recommendation(result)

        return result

    def _generate_summary(self, intel_data: dict, entities: list) -> str:
        """生成分析摘要（规则版本）"""
        intel_type = intel_data.get("intel_type", "未知")
        country = intel_data.get("country", "未知")
        event_date = intel_data.get("event_date", "")

        # 构建摘要
        unit_list = [e.get("text", "") for e in entities if e.get("type") == "unit"]
        location_list = [e.get("text", "") for e in entities if e.get("type") == "location"]

        unit_str = "、".join(unit_list[:3]) if unit_list else "未识别"
        location_str = "、".join(location_list[:2]) if location_list else "未识别"

        summary = f"【{intel_type}】{country}方面在{event_date}有军事动态。"
        if unit_str:
            summary += f"涉及单位：{unit_str}。"
        if location_str:
            summary += f"涉及区域：{location_str}。"

        return summary

    def _check_abnormal(self, text: str, intel_data: dict) -> bool:
        """判断是否异常"""
        # 异常关键词
        abnormal_keywords = [
            "异常集结", "大规模调动", "紧急部署", "撤侨", "撤离外交",
            "戒严", "宵禁", "战争状态", "总动员", "临战",
        ]
        for keyword in abnormal_keywords:
            if keyword in text:
                return True
        return False

    def _check_warning(self, text: str, intel_data: dict) -> bool:
        """判断是否需要预警"""
        # 预警关键词
        warning_keywords = [
            "开战", "进攻", "袭击", "冲突", "战争",
            "导弹", "核", "生化", "大量伤亡",
        ]
        for keyword in warning_keywords:
            if keyword in text:
                return True
        # 如果异常但不确定是否预警
        if self._check_abnormal(text, intel_data):
            return True
        return False

    def _calculate_confidence(self, intel_data: dict, entities: list) -> float:
        """计算置信度（0.0~1.0）"""
        confidence = 0.5

        # 来源可靠性加成
        source_reliability = intel_data.get("source_reliability", "C")
        reliability_map = {"A": 0.9, "B": 0.75, "C": 0.5, "D": 0.3}
        confidence = reliability_map.get(source_reliability, 0.5)

        # 可信度等级加成
        credibility = intel_data.get("credibility", "possible")
        credibility_map = {"confirmed": 0.2, "probable": 0.1, "possible": 0.0, "doubtful": -0.1}
        confidence += credibility_map.get(credibility, 0.0)

        # 实体数量加成（多实体=更可信）
        if len(entities) >= 3:
            confidence += 0.1
        elif len(entities) == 0:
            confidence -= 0.2

        return max(0.0, min(1.0, confidence))

    def _generate_recommendation(self, result: dict) -> str:
        """生成采纳建议"""
        confidence = result["confidence"]
        is_abnormal = result["is_abnormal"]
        is_warning = result["is_warning"]

        if confidence >= 0.8:
            if is_warning:
                return "高置信度预警，建议立即核实并通知值班人员"
            return "高置信度情报，建议直接采纳入库"
        elif confidence >= 0.7:
            if is_warning:
                return "中高置信度预警，建议优先核实后采纳"
            return "建议采纳入库"
        elif confidence >= 0.5:
            return "中等置信度，建议人工复核后决定是否采纳"
        else:
            return "低置信度，建议搁置或进一步核实后再处理"

    def save_analysis_result(self, intel_id: str, result: dict):
        """保存分析结果到数据库"""
        try:
            with get_cursor() as cur:
                analysis_json = json.dumps(result, ensure_ascii=False)
                cur.execute(
                    """
                    UPDATE intelligence
                    SET analysis_result = %s, updated_at = %s
                    WHERE intel_id = %s
                    """,
                    (analysis_json, datetime.now(), intel_id)
                )
        except Exception as e:
            print(f"保存分析结果失败: {e}")

    def auto_analyze_new_intel(self, limit: int = 10):
        """自动分析未处理的新情报"""
        try:
            with get_cursor() as cur:
                # 查询未分析的情报（analysis_result 为空）
                cur.execute(
                    """
                    SELECT intel_id, title, content, intel_type, event_date,
                           country, source_reliability, credibility
                    FROM intelligence
                    WHERE analysis_result IS NULL
                    ORDER BY obtained_date DESC
                    LIMIT %s
                    """,
                    (limit,)
                )
                rows = cur.fetchall()

            results = []
            for row in rows:
                intel_data = {
                    "intel_id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "intel_type": row[3],
                    "event_date": str(row[4]) if row[4] else "",
                    "country": row[5],
                    "source_reliability": row[6],
                    "credibility": row[7],
                }
                result = self.analyze_intelligence(intel_data)
                self.save_analysis_result(intel_data["intel_id"], result)
                results.append(result)

            return results
        except Exception as e:
            print(f"自动分析失败: {e}")
            return []
