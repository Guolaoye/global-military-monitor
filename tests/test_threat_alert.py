"""测试威胁预警模块"""
import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestAlertLevel(unittest.TestCase):
    """测试预警级别"""

    def test_alert_level_import(self):
        """测试预警级别导入"""
        from src.threat_alert.rules import AlertLevel
        self.assertEqual(AlertLevel.URGENT.value, "紧急")
        self.assertEqual(AlertLevel.HIGH.value, "高")
        self.assertEqual(AlertLevel.MEDIUM.value, "中")
        self.assertEqual(AlertLevel.LOW.value, "低")

    def test_color_mapping(self):
        """测试颜色映射"""
        from src.threat_alert.rules import AlertLevel
        self.assertEqual(AlertLevel.URGENT.color, "red")
        self.assertEqual(AlertLevel.HIGH.color, "orange")
        self.assertEqual(AlertLevel.MEDIUM.color, "yellow")
        self.assertEqual(AlertLevel.LOW.color, "blue")


class TestAlertRule(unittest.TestCase):
    """测试预警规则"""

    def test_rule_import(self):
        """测试规则导入"""
        from src.threat_alert.rules import AlertRule
        rule = AlertRule("测试规则", lambda d: False, "测试描述")
        self.assertIsNotNone(rule)


class TestFeishuCard(unittest.TestCase):
    """测试飞书卡片"""

    def test_card_import(self):
        """测试卡片模块导入"""
        from src.threat_alert.feishu_card import build_alert_card
        card = build_alert_card("紧急", "测试预警", "测试描述")
        self.assertIsNotNone(card)
        self.assertIsInstance(card, dict)


class TestThreatAlertManager(unittest.TestCase):
    """测试威胁预警管理器"""

    def test_manager_import(self):
        """测试管理器导入"""
        from src.threat_alert.manager import ThreatAlertManager
        mgr = ThreatAlertManager()
        self.assertIsNotNone(mgr)

    def test_get_active_alerts_empty(self):
        """测试空预警列表"""
        from src.threat_alert.manager import ThreatAlertManager
        mgr = ThreatAlertManager()
        alerts = mgr.get_active_alerts()
        self.assertIsInstance(alerts, list)


class TestThreatAnalyzer(unittest.TestCase):
    """测试威胁分析器"""

    def test_analyzer_import(self):
        """测试分析器导入"""
        from src.threat_alert.analyzer import ThreatAnalyzer
        analyzer = ThreatAnalyzer()
        self.assertIsNotNone(analyzer)

    def test_calculate_threat_score(self):
        """测试威胁评分计算"""
        from src.threat_alert.analyzer import ThreatAnalyzer
        analyzer = ThreatAnalyzer()
        score = analyzer.calculate_threat_score({"concentration_score": 0.5, "movement_score": 0.3})
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
