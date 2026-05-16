"""测试AI情报分析引擎"""
import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestEntityExtractor(unittest.TestCase):
    """测试实体提取器"""

    def test_extract_unit(self):
        """测试单位番号提取"""
        from src.ai_engine.entity_extractor import EntityExtractor
        extractor = EntityExtractor()
        text = "解放军东部战区海军在南海进行演习"
        entities = extractor.extract(text)
        unit_entities = [e for e in entities if e["type"] == "unit"]
        self.assertGreater(len(unit_entities), 0)

    def test_extract_location(self):
        """测试位置提取"""
        from src.ai_engine.entity_extractor import EntityExtractor
        extractor = EntityExtractor()
        text = "航母编队在东海执行任务"
        entities = extractor.extract(text)
        loc_entities = [e for e in entities if e["type"] == "location"]
        self.assertGreater(len(loc_entities), 0)

    def test_extract_equipment(self):
        """测试装备型号提取"""
        from src.ai_engine.entity_extractor import EntityExtractor
        extractor = EntityExtractor()
        text = "J-20战机和052D驱逐舰参与演习"
        entities = extractor.extract(text)
        eq_entities = [e for e in entities if e["type"] == "equipment"]
        self.assertGreater(len(eq_entities), 0)


class TestCrossValidator(unittest.TestCase):
    """测试交叉验证器"""

    def test_calculate_credibility(self):
        """测试置信度计算"""
        from src.ai_engine.cross_validator import CrossValidator
        validator = CrossValidator()
        intel_list = [
            {"source_reliability": "A", "intel_type": "movement", "event_date": "2024-01-01"},
            {"source_reliability": "A", "intel_type": "movement", "event_date": "2024-01-01"},
        ]
        score = validator.calculate_credibility(intel_list)
        self.assertGreaterEqual(score, 0.6)

    def test_suggest_approval(self):
        """测试采纳建议"""
        from src.ai_engine.cross_validator import CrossValidator
        validator = CrossValidator()
        intel = {"source_reliability": "A", "credibility": "confirmed"}
        suggestion = validator.suggest_approval(intel)
        self.assertIsInstance(suggestion, str)


class TestRAGRetriever(unittest.TestCase):
    """测试RAG检索器"""

    def test_retriever_import(self):
        """测试检索器导入"""
        from src.ai_engine.rag_retriever import RAGRetriever
        retriever = RAGRetriever()
        self.assertIsNotNone(retriever)

    def test_build_context_empty(self):
        """测试空查询上下文"""
        from src.ai_engine.rag_retriever import RAGRetriever
        retriever = RAGRetriever()
        context = retriever.build_context("不存在的信息")
        self.assertIsInstance(context, str)


class TestSituationAdvisor(unittest.TestCase):
    """测试态势顾问"""

    def test_advise_real_empty(self):
        """测试空态势建议"""
        from src.ai_engine.situation_advisor import SituationAdvisor
        advisor = SituationAdvisor()
        result = advisor.advise_real([])
        self.assertIsInstance(result, dict)
        self.assertIn("next_moves", result)

    def test_detect_anomaly_empty(self):
        """测试空异常检测"""
        from src.ai_engine.situation_advisor import SituationAdvisor
        advisor = SituationAdvisor()
        result = advisor.detect_anomaly([])
        self.assertEqual(result, [])


class TestChatInterface(unittest.TestCase):
    """测试聊天接口"""

    def test_chat_import(self):
        """测试聊天接口导入"""
        from src.ai_engine.chat import ChatInterface
        chat = ChatInterface()
        self.assertIsNotNone(chat)

    def test_mock_response(self):
        """测试无API时的Mock回复"""
        from src.ai_engine.chat import ChatInterface
        chat = ChatInterface()
        chat.api_key = ""  # 确保无API key
        response = chat.chat("测试消息")
        self.assertIn("API Key", response)


class TestMiniMaxClient(unittest.TestCase):
    """测试MiniMax客户端"""

    def test_client_import(self):
        """测试客户端导入"""
        from src.ai_engine.minimax_client import MiniMaxClient
        client = MiniMaxClient()
        self.assertIsNotNone(client)

    def test_mock_response(self):
        """测试Mock回复"""
        client = __import__("src.ai_engine.minimax_client", fromlist=["MiniMaxClient"]).MiniMaxClient()
        client.api_key = ""
        response = client.chat([{"role": "user", "content": "hello"}])
        self.assertIsInstance(response, str)


if __name__ == "__main__":
    unittest.main()
