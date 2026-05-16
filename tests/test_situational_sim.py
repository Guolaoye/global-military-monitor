"""测试模拟态势推演模块"""
import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestSimSituationEngine(unittest.TestCase):
    """测试模拟态势引擎"""

    def test_engine_import(self):
        """测试引擎导入"""
        from src.situational_sim.engine import SimSituationEngine
        engine = SimSituationEngine()
        self.assertIsNotNone(engine)
        self.assertFalse(engine.is_running)

    def test_data_protection(self):
        """测试数据保护约束"""
        from src.situational_sim.engine import SimSituationEngine
        engine = SimSituationEngine()
        # 启动模拟
        engine.start_simulation()
        self.assertTrue(engine.is_running)
        self.assertIsNotNone(engine.sim_units)
        # 结束模拟
        engine.end_simulation()
        self.assertFalse(engine.is_running)


class TestSimUnitManager(unittest.TestCase):
    """测试模拟单位管理"""

    def test_unit_manager_import(self):
        """测试单位管理器导入"""
        from src.situational_sim.unit_manager import SimUnitManager
        mgr = SimUnitManager()
        self.assertIsNotNone(mgr)

    def test_add_unit(self):
        """测试添加临时单位"""
        from src.situational_sim.unit_manager import SimUnitManager
        mgr = SimUnitManager()
        unit_data = {"unit_id": "sim_001", "name": "红军部队", "side": "red", "combat_power": 0.8}
        result = mgr.add_unit(unit_data)
        self.assertTrue(result)
        self.assertIn("sim_001", mgr.get_units())


class TestWeatherEffectCalculator(unittest.TestCase):
    """测试天气效果计算"""

    def test_weather_calculator_import(self):
        """测试天气计算器导入"""
        from src.situational_sim.weather_effect import WeatherEffectCalculator
        calc = WeatherEffectCalculator()
        self.assertIsNotNone(calc)


class TestBattleSimulator(unittest.TestCase):
    """测试战斗模拟"""

    def test_battle_simulator_import(self):
        """测试战斗模拟器导入"""
        from src.situational_sim.battle_sim import BattleSimulator
        sim = BattleSimulator()
        self.assertIsNotNone(sim)

    def test_force_ratio_calculation(self):
        """测试力量对比计算"""
        from src.situational_sim.battle_sim import BattleSimulator
        sim = BattleSimulator()
        side_a = [{"combat_power": 0.8}, {"combat_power": 0.6}]
        side_b = [{"combat_power": 0.7}]
        ratio = sim.calculate_force_ratio(side_a, side_b)
        self.assertGreater(ratio, 1.0)


if __name__ == "__main__":
    unittest.main()
