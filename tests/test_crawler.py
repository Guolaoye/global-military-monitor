"""爬虫模块测试"""
import unittest
from src.crawler.confidence import ConfidenceCalculator
from src.crawler.deduplicator import Deduplicator
from datetime import datetime

class TestCrawler(unittest.TestCase):
    
    def test_confidence_calculator(self):
        """测试置信度计算"""
        score = ConfidenceCalculator.calculate(0.7, multi_source_count=3)
        self.assertGreaterEqual(score, 0.7)
        
        score = ConfidenceCalculator.calculate(1.0, is_exclusive=True)
        self.assertLessEqual(score, 0.9)
    
    def test_deduplicator(self):
        """测试去重器"""
        dedup = Deduplicator()
        ts = datetime.now()
        
        self.assertFalse(dedup.is_duplicate("unit1", "movement", ts))
        self.assertTrue(dedup.is_duplicate("unit1", "movement", ts))
        self.assertFalse(dedup.is_duplicate("unit2", "movement", ts))

if __name__ == "__main__":
    unittest.main()
