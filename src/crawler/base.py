"""爬虫基类（适配器模式）"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class ParseResult:
    """解析结果数据类"""
    unit_id: Optional[str] = None
    event_type: str = ""
    title: str = ""
    content: str = ""
    source_url: str = ""
    source_type: str = ""
    confidence: float = 0.5
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_date: Optional[datetime] = None

class BaseAdapter(ABC):
    """爬虫适配器基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def fetch(self) -> list[ParseResult]:
        """抓取数据，返回解析结果列表"""
        pass
    
    def validate_result(self, result: ParseResult) -> bool:
        """验证解析结果的有效性"""
        if not result.title:
            return False
        if result.confidence < 0 or result.confidence > 1:
            return False
        return True
