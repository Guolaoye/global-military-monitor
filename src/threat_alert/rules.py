import sys
from pathlib import Path
from enum import Enum
from typing import Dict, Any, Callable, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class AlertLevel(Enum):
    """告警级别枚举"""
    CRITICAL = "紧急"    # 即将开战（异常集结、撤离外交人员等前置信号）
    HIGH = "高"          # 强弱态势逆转
    MEDIUM = "中"        # 大幅战略扩张或收缩
    LOW = "低"           # 即将结束
    
    @property
    def color(self) -> str:
        """获取告警级别对应的颜色"""
        colors = {
            AlertLevel.CRITICAL: "red",
            AlertLevel.HIGH: "orange",
            AlertLevel.MEDIUM: "yellow",
            AlertLevel.LOW: "blue"
        }
        return colors.get(self, "grey")
    
    @property
    def feishu_color(self) -> str:
        """飞书卡片颜色"""
        colors = {
            AlertLevel.CRITICAL: "red",
            AlertLevel.HIGH: "orange",
            AlertLevel.MEDIUM: "yellow",
            AlertLevel.LOW: "blue"
        }
        return colors.get(self, "grey")


class AlertRule:
    """告警规则类"""
    
    def __init__(
        self, 
        name: str, 
        level: AlertLevel, 
        condition_func: Callable[[Dict[str, Any]], bool],
        description: str
    ):
        self.name = name
        self.level = level
        self.condition_func = condition_func
        self.description = description
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """评估条件是否满足"""
        try:
            return self.condition_func(data)
        except Exception:
            return False
    
    def __repr__(self):
        return f"AlertRule(name={self.name}, level={self.level.value})"


def _check_war_imminent(data: Dict[str, Any]) -> bool:
    """检测即将开战信号"""
    keywords = [
        "撤离外交人员", "外交人员撤离", "撤侨", "撤离侨民",
        "异常集结", "军队集结", "兵力集结", "大规模集结",
        "战争动员", "军事动员", "总动员",
        "紧急状态", "戒严", "宵禁",
        "导弹部署", "核武器部署", "核打击准备"
    ]
    text = str(data.get("content", "")).lower() + str(data.get("description", "")).lower()
    return any(kw in text for kw in keywords)


def _check_power_reversal(data: Dict[str, Any]) -> bool:
    """检测强弱态势逆转"""
    force_ratio = data.get("force_ratio_change", 0)
    return abs(force_ratio) > 0.3  # 30%以上的力量对比变化


def _check_expansion(data: Dict[str, Any]) -> bool:
    """检测战略扩张"""
    movement = data.get("movement_direction", "")
    troops = data.get("troop_movement", 0)
    return movement == "outward" and troops > 500


def _check_contraction(data: Dict[str, Any]) -> bool:
    """检测战略收缩"""
    movement = data.get("movement_direction", "")
    troops = data.get("troop_movement", 0)
    return movement == "inward" and troops > 500


def _check_conflict_ending(data: Dict[str, Any]) -> bool:
    """检测冲突即将结束"""
    activity_level = data.get("activity_level", 100)
    trend = data.get("activity_trend", 0)
    return activity_level < 30 and trend < -0.1


# 预定义告警规则
RULE_WAR_IMMINENT = AlertRule(
    name="即将开战",
    level=AlertLevel.CRITICAL,
    condition_func=_check_war_imminent,
    description="检测到异常集结、撤离外交人员等战争前置信号"
)

RULE_POWER_REVERSAL = AlertRule(
    name="强弱态势逆转",
    level=AlertLevel.HIGH,
    condition_func=_check_power_reversal,
    description="力量对比发生显著逆转"
)

RULE_STRATEGIC_EXPANSION = AlertRule(
    name="大幅战略扩张",
    level=AlertLevel.MEDIUM,
    condition_func=_check_expansion,
    description="检测到大规模向外兵力调动"
)

RULE_STRATEGIC_CONTRACTION = AlertRule(
    name="大幅战略收缩",
    level=AlertLevel.MEDIUM,
    condition_func=_check_contraction,
    description="检测到大规模向内兵力调动"
)

RULE_CONFLICT_ENDING = AlertRule(
    name="即将结束",
    level=AlertLevel.LOW,
    condition_func=_check_conflict_ending,
    description="活动水平显著下降，冲突可能即将结束"
)


# 所有预定义规则列表
ALL_RULES: List[AlertRule] = [
    RULE_WAR_IMMINENT,
    RULE_POWER_REVERSAL,
    RULE_STRATEGIC_EXPANSION,
    RULE_STRATEGIC_CONTRACTION,
    RULE_CONFLICT_ENDING,
]
