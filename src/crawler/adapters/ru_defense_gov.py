"""俄罗斯国防部官网适配器"""
from src.crawler.base import BaseAdapter, ParseResult
import requests
import logging

logger = logging.getLogger(__name__)

class RuDefenseGovAdapter(BaseAdapter):
    """俄罗斯国防部官网 (mil.ru) 适配器"""
    
    def __init__(self):
        super().__init__("ru_defense_gov")
        self.base_url = "https://mil.ru"
    
    def fetch(self) -> list[ParseResult]:
        """抓取俄罗斯国防部新闻"""
        results = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; GlobalMilitaryMonitor/1.0)"}
            resp = requests.get(self.base_url, headers=headers, timeout=15)
            logger.info(f"俄罗斯国防部新闻抓取: HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"俄罗斯国防部新闻抓取失败: {e}")
        return results
