"""测试设置模块"""
import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestSettingsManager(unittest.TestCase):
    """测试设置管理器"""

    def test_manager_import(self):
        """测试管理器导入"""
        from src.settings.manager import SettingsManager
        mgr = SettingsManager()
        self.assertIsNotNone(mgr)

    def test_get_default(self):
        """测试默认配置获取"""
        from src.settings.manager import SettingsManager
        mgr = SettingsManager()
        val = mgr.get("AI_MODEL", "mini-max")
        self.assertIsNotNone(val)


class TestConfigValidator(unittest.TestCase):
    """测试配置验证器"""

    def test_validator_import(self):
        """测试验证器导入"""
        from src.settings.config import ConfigValidator
        v = ConfigValidator()
        self.assertIsNotNone(v)

    def test_crawler_interval_valid(self):
        """测试爬虫间隔验证"""
        from src.settings.config import ConfigValidator
        v = ConfigValidator()
        self.assertTrue(v.validate_crawler_interval(3))
        self.assertFalse(v.validate_crawler_interval(0))
        self.assertFalse(v.validate_crawler_interval(10))


class TestAIModelConfig(unittest.TestCase):
    """测试AI模型配置"""

    def test_ai_model_config_import(self):
        """测试AI模型配置导入"""
        from src.settings.ai_model import AIModelConfig
        cfg = AIModelConfig()
        self.assertIsNotNone(cfg)

    def test_get_models(self):
        """测试获取模型列表"""
        from src.settings.ai_model import AIModelConfig
        cfg = AIModelConfig()
        models = cfg.get_models()
        self.assertIsInstance(models, list)
        self.assertIn("MiniMax MoE", models)


if __name__ == "__main__":
    unittest.main()
