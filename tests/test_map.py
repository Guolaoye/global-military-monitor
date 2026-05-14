"""地图模块测试"""
import unittest

class TestMap(unittest.TestCase):
    
    def test_icon_manager(self):
        """测试图标管理器"""
        from src.map.icon_manager import IconManager
        manager = IconManager()
        manager.add_icon("icon1", 35.0, 105.0, "army", "unit1")
        self.assertEqual(len(manager.active_icons), 1)
        manager.remove_icon("icon1")
        self.assertEqual(len(manager.active_icons), 0)
    
    def test_overlay(self):
        """测试叠加层"""
        from src.map.overlay import OverlayManager
        manager = OverlayManager()
        manager.add_icon_layer([{"id": "i1", "lat": 35, "lng": 105}])
        self.assertEqual(len(manager.layers["icons"]), 1)

if __name__ == "__main__":
    unittest.main()
