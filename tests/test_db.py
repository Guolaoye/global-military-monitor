"""数据库模块测试"""
import unittest

class TestDB(unittest.TestCase):
    
    def test_connection(self):
        """测试数据库连接"""
        from src.db.connection import test_connection
        # 跳过实际测试（需要真实数据库）
        pass
    
    def test_models(self):
        """测试模型定义"""
        from src.db.models import Country, Unit, Equipment
        # 测试模型字段存在
        self.assertTrue(hasattr(Country, "__tablename__"))
        self.assertTrue(hasattr(Unit, "unit_id"))
        self.assertTrue(hasattr(Equipment, "equipment_id"))

if __name__ == "__main__":
    unittest.main()
