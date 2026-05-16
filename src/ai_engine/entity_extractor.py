"""军事实体提取器"""
import re
from typing import List, Dict


class EntityExtractor:
    """军事实体提取器（基于正则规则）"""

    def __init__(self):
        # 编译正则表达式
        self._compile_patterns()

    def _compile_patterns(self):
        """编译实体提取正则"""
        # 单位番号
        self.unit_patterns = [
            re.compile(r'[东南西北中]部战区[海军空军陆军]?'),
            re.compile(r'第[一二三四五六七八九十百]+[舰队师团旅营连排]'),
            re.compile(r'[海陆空]军[第]?[一二三四五六七八九十]+[舰队师团旅营]'),
            re.compile(r'航空母舰[编队群]'),
            re.compile(r'驱逐舰[第]?[1-9][0-9]*号'),
            re.compile(r'护卫舰[第]?[1-9][0-9]*号'),
            re.compile(r'战略[核]?[轰炸机部队]'),
            re.compile(r'防空[导弹旅旅]'),
        ]

        # 地理位置
        self.location_patterns = [
            re.compile(r'[东北西南]海'),
            re.compile(r'[台湾海峡朝鲜半岛]'),
            re.compile(r'[冲绳横须贺佐世保]'),
            re.compile(r'[南海黄海渤海]'),
            re.compile(r'[中东波斯湾红海]'),
            re.compile(r'[地中海黑海]'),
            re.compile(r'〔[0-9]{1,2}°[0-9]+′[NS]?[，,][0-9]{1,3}°[0-9]+′[EW]?〕'),
        ]

        # 行动类型
        self.action_patterns = [
            re.compile(r'[军事]?演习|演练|操演'),
            re.compile(r'远海[训练航行]'),
            re.compile(r'[实弹射击]训练'),
            re.compile(r'部署|调动|转移'),
            re.compile(r'[联合]军演'),
            re.compile(r'巡航[导弹]?[制海制空]?'),
            re.compile(r'舰载机[起降飞行]'),
        ]

        # 装备型号
        self.equipment_patterns = [
            re.compile(r'J-[12][0-9]'),
            re.compile(r'J-[1-9]'),
            re.compile(r'歼[-]?[12][0-9]'),
            re.compile(r'F-[12][0-9][A-Z]?'),
            re.compile(r'052D?[驱逐舰]'),
            re.compile(r'055[驱逐舰]'),
            re.compile(r'094[核潜艇]'),
            re.compile(r'093[核潜艇]'),
            re.compile(r'辽宁舰|山东舰|福建舰'),
            re.compile(r'东风[-]?[12][0-9]'),
            re.compile(r'长剑[-]?10'),
            re.compile(r'鹰击[-]?[12][0-9]'),
        ]

        # 时间表达式
        self.time_patterns = [
            re.compile(r'[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日'),
            re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}'),
            re.compile(r'[0-9]{1,2}时[0-9]{2}分'),
            re.compile(r'昨日|今日|明日|近日'),
            re.compile(r'当地时间|北京时间'),
        ]

    def extract(self, text: str) -> List[Dict]:
        """
        从文本中提取军事实体

        Returns:
            List of entity dicts: [{"type": "unit"|"location"|"action"|"equipment"|"time", "text": "...", "start": N, "end": N}]
        """
        entities = []

        # 单位提取
        for pattern in self.unit_patterns:
            for match in pattern.finditer(text):
                entities.append({
                    "type": "unit",
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })

        # 位置提取
        for pattern in self.location_patterns:
            for match in pattern.finditer(text):
                entities.append({
                    "type": "location",
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })

        # 行动类型提取
        for pattern in self.action_patterns:
            for match in pattern.finditer(text):
                entities.append({
                    "type": "action",
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })

        # 装备型号提取
        for pattern in self.equipment_patterns:
            for match in pattern.finditer(text):
                entities.append({
                    "type": "equipment",
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })

        # 时间表达式提取
        for pattern in self.time_patterns:
            for match in pattern.finditer(text):
                entities.append({
                    "type": "time",
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })

        # 去重并按位置排序
        seen = set()
        unique_entities = []
        for e in entities:
            key = (e["type"], e["text"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)
        unique_entities.sort(key=lambda x: x["start"])

        return unique_entities

    def normalize(self, entity: Dict) -> str:
        """标准化实体名称"""
        text = entity.get("text", "")
        etype = entity.get("type", "")

        if etype == "unit":
            # 标准化番号
            text = text.replace("海军", "").replace("空军", "").replace("陆军", "")
            # 处理数字
            text = re.sub(r'[一二三四五六七八九十]+', lambda m: str(self._cn_to_arabic(m.group())), text)

        elif etype == "location":
            # 保持原样，但做标准化映射
            location_map = {
                "东海": "东中国海",
                "南海": "南中国海",
                "海峡": "台湾海峡",
            }
            for k, v in location_map.items():
                if k in text:
                    text = text.replace(k, v)

        return text

    def _cn_to_arabic(self, cn: str) -> int:
        """中文数字转阿拉伯数字"""
        cn_map = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
            "百": 100,
        }
        total = 0
        for c in cn:
            total = total * 10 + cn_map.get(c, 0)
        return total if total > 0 else 10
