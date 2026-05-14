"""置信度计算器"""
from enum import Enum

class SourceReliability(Enum):
    """来源可靠性枚举"""
    OFFICIAL = 1.0      # 官方来源
    MEDIA_100K = 0.7    # 粉丝10万+自媒体
    CIVIL_DATA = 0.5    # 民间数据站
    OSINT = 0.3          # 其他开源情报

class ConfidenceCalculator:
    """置信度计算器"""
    
    @staticmethod
    def calculate(base_score: float, multi_source_count: int = 0, is_exclusive: bool = False) -> float:
        """
        计算最终置信度
        
        Args:
            base_score: 基础分（根据来源类型）
            multi_source_count: 多源交叉验证的来源数量
            is_exclusive: 是否单源独家
        Returns:
            float: 最终置信度 (0.0 ~ 1.0)
        """
        score = base_score
        
        # 多源交叉验证（≥3个不同来源确认）：+0.2
        if multi_source_count >= 3:
            score += 0.2
        
        # 单源独家：-0.1
        if is_exclusive:
            score -= 0.1
        
        # 限制范围
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def from_source_type(source_type: str) -> float:
        """根据来源类型获取基础分"""
        source_map = {
            "official": 1.0,
            "media_100k": 0.7,
            "civil_data": 0.5,
            "osint": 0.3,
        }
        return source_map.get(source_type.lower(), 0.5)
