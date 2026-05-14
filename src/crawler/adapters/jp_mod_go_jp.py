"""日本防卫省官网适配器"""
from src.crawler.base import BaseAdapter, ParseResult
import requests
import logging

logger = logging.getLogger(__name__)

class JpModGoJpAdapter(BaseAdapter):
    """日本防卫省官网 (mod.go.jp) 适配器"""
    
    def __init__(self):
        super().__init__("jp_mod_go_jp")
        self.base_url = "https://www.mod.go.jp"
    
    def fetch(self) -> list[ParseResult]:
        """抓取日本防卫省新闻"""
        results = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; GlobalMilitaryMonitor/1.0)"}
            resp = requests.get(self.base_url, headers=headers, timeout=15)
            logger.info(f"日本防卫省新闻抓取: HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"日本防卫省新闻抓取失败: {e}")
        return results
