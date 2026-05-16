"""测试真实态势推演模块"""
import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestTimelineManager(unittest.TestCase):
    """测试时间轴管理器"""

    def test_timeline_import(self):
        """测试时间轴模块导入"""
        from src.situational_real.timeline import TimelineManager
        tm = TimelineManager()
        self.assertIsNotNone(tm)

    def test_get_positions_at_time_empty(self):
        """测试空时间点查询"""
        from src.situational_real.timeline import TimelineManager
        tm = TimelineManager()
        result = tm.get_positions_at_time("2024-01-01")
        self.assertEqual(result, [])


class TestAffectedUnitsAnalyzer(unittest.TestCase):
    """测试受影响单位分析"""

    def test_haversine_distance(self):
        """测试 Haversine 距离计算"""
        from src.situational_real.affected_units import AffectedUnitsAnalyzer
        analyzer = AffectedUnitsAnalyzer()
        # 北京到上海约 1060km
        dist = analyzer._haversine(39.9, 116.4, 31.2, 121.5)
        self.assertGreater(dist, 1000)
        self.assertLess(dist, 1100)

    def test_analyze_point_empty(self):
        """测试空点分析"""
        from src.situational_real.affected_units import AffectedUnitsAnalyzer
        analyzer = AffectedUnitsAnalyzer()
        result = analyzer.analyze_point(0, 0)
        self.assertIsInstance(result, list)


class TestTerrainAnalysis(unittest.TestCase):
    """测试地形分析"""

    def test_terrain_import(self):
        """测试地形分析模块导入"""
        from src.situational_real.terrain_analysis import TerrainAnalysis
        ta = TerrainAnalysis()
        self.assertIsNotNone(ta)

    def test_analyze_returns_dict(self):
        """测试分析返回字典"""
        from src.situational_real.terrain_analysis import TerrainAnalysis
        ta = TerrainAnalysis()
        result = ta.analyze(39.9, 116.4)
        self.assertIsInstance(result, dict)
        self.assertIn("terrain_score", result)


class TestAIAssistant(unittest.TestCase):
    """测试AI辅助分析"""

    def test_ai_assistant_import(self):
        """测试AI辅助模块导入"""
        from src.situational_real.ai_assistant import AIAssistant
        ai = AIAssistant()
        self.assertIsNotNone(ai)


if __name__ == "__main__":
    unittest.main()
