import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.connection import get_cursor
from src.db.models import Intelligence, Alert


class ThreatAnalyzer:
    """威胁分析器"""
    
    def __init__(self, lookback_hours: int = 24):
        self.lookback_hours = lookback_hours
    
    def analyze_intelligence_trends(self) -> List[Dict[str, Any]]:
        """
        分析近期情报数据，检测趋势
        
        Returns:
            趋势分析结果列表
        """
        trends = []
        cutoff = datetime.now() - timedelta(hours=self.lookback_hours)
        
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, content, country_id, latitude, longitude, 
                           created_at, source_type
                    FROM intelligence 
                    WHERE created_at >= %s AND is_active = true
                    ORDER BY created_at DESC
                """, (cutoff,))
                
                rows = cursor.fetchall()
                if not rows:
                    return trends
                
                # 按内容关键词检测趋势
                trend_indicators = self._detect_trends(rows)
                trends.extend(trend_indicators)
                
                # 检测位置聚集
                concentration = self._check_position_concentration(rows)
                if concentration:
                    trends.append(concentration)
                    
        except Exception as e:
            print(f"[ThreatAnalyzer] 分析失败: {e}")
        
        return trends
    
    def _detect_trends(self, rows: List[tuple]) -> List[Dict[str, Any]]:
        """检测情报内容中的趋势关键词"""
        trends = []
        
        keywords_map = {
            "撤离": {"type": "撤离", "level": "紧急"},
            "撤侨": {"type": "撤侨", "level": "紧急"},
            "集结": {"type": "集结", "level": "紧急"},
            "动员": {"type": "动员", "level": "紧急"},
            "扩张": {"type": "扩张", "level": "中"},
            "收缩": {"type": "收缩", "level": "中"},
            "增兵": {"type": "增兵", "level": "中"},
            "撤兵": {"type": "撤兵", "level": "低"},
            "停火": {"type": "停火", "level": "低"},
            "谈判": {"type": "谈判", "level": "低"},
        }
        
        for row in rows:
            intel_id, title, content, country_id, lat, lng, created_at, source = row
            text = f"{title} {content}".lower()
            
            for kw, info in keywords_map.items():
                if kw in text:
                    trends.append({
                        "type": info["type"],
                        "level": info["level"],
                        "intel_id": intel_id,
                        "text": f"{title}",
                        "country_id": country_id,
                        "latitude": lat,
                        "longitude": lng,
                        "timestamp": created_at.isoformat() if created_at else None
                    })
                    break
        
        return trends
    
    def _check_position_concentration(self, rows: List[tuple]) -> Optional[Dict[str, Any]]:
        """检查位置聚集情况"""
        positions = [(r[4], r[5]) for r in rows if r[4] and r[5]]
        
        if len(positions) < 3:
            return None
        
        lats = [p[0] for p in positions]
        lngs = [p[1] for p in positions]
        
        # 计算标准差
        lat_std = statistics.stdev(lats) if len(lats) > 1 else 0
        lng_std = statistics.stdev(lngs) if len(lngs) > 1 else 0
        
        # 标准差小于0.5度表示位置集中
        if lat_std < 0.5 and lng_std < 0.5:
            center_lat = statistics.mean(lats)
            center_lng = statistics.mean(lngs)
            return {
                "type": "异常集结",
                "level": "紧急",
                "latitude": center_lat,
                "longitude": center_lng,
                "count": len(positions)
            }
        
        return None
    
    def detect_anomaly(self) -> List[Dict[str, Any]]:
        """
        统计异常检测 - 检测偏离正常模式的活动
        
        Returns:
            异常列表
        """
        anomalies = []
        cutoff = datetime.now() - timedelta(hours=self.lookback_hours * 7)  # 一周
        
        try:
            with get_cursor() as cursor:
                # 获取近7天数据计算基线
                cursor.execute("""
                    SELECT COUNT(*) as count, DATE(created_at) as date
                    FROM intelligence
                    WHERE created_at >= %s
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """, (cutoff,))
                
                rows = cursor.fetchall()
                if len(rows) < 3:
                    return anomalies
                
                counts = [r[0] for r in rows]
                mean_count = statistics.mean(counts)
                stdev_count = statistics.stdev(counts) if len(counts) > 1 else 0
                
                # 获取今天的数量
                today = datetime.now().date()
                today_count = sum(1 for r in rows if r[1] == today)
                
                # 检测异常（超过2个标准差）
                if stdev_count > 0 and today_count > mean_count + 2 * stdev_count:
                    anomalies.append({
                        "type": "活动异常增多",
                        "level": "高",
                        "detail": f"今日情报数量({today_count})显著高于平均水平({mean_count:.0f})"
                    })
                    
        except Exception as e:
            print(f"[ThreatAnalyzer] 异常检测失败: {e}")
        
        return anomalies
    
    def check_unit_concentration(self, unit_ids: List[int]) -> Optional[Dict[str, Any]]:
        """
        检测单元是否异常聚集
        
        Args:
            unit_ids: 单元ID列表
        
        Returns:
            聚集信息或None
        """
        if not unit_ids:
            return None
        
        try:
            with get_cursor() as cursor:
                placeholders = ','.join(['%s'] * len(unit_ids))
                cursor.execute(f"""
                    SELECT latitude, longitude, COUNT(*) as cnt
                    FROM intelligence
                    WHERE unit_id IN ({placeholders})
                    AND created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY latitude, longitude
                    HAVING COUNT(*) > 3
                """, tuple(unit_ids))
                
                clusters = cursor.fetchall()
                if clusters:
                    # 返回最大的聚集点
                    largest = max(clusters, key=lambda x: x[2])
                    return {
                        "type": "单元异常聚集",
                        "level": "紧急",
                        "latitude": largest[0],
                        "longitude": largest[1],
                        "count": largest[2]
                    }
                    
        except Exception as e:
            print(f"[ThreatAnalyzer] 单元聚集检测失败: {e}")
        
        return None
    
    def calculate_threat_score(self, unit_id: Optional[int] = None) -> int:
        """
        计算威胁评分 (0-100)
        
        Args:
            unit_id: 可选的单元ID
        
        Returns:
            威胁评分 0-100
        """
        score = 0
        
        # 分析趋势获取分数
        trends = self.analyze_intelligence_trends()
        for trend in trends:
            level = trend.get("level", "低")
            if level == "紧急":
                score += 30
            elif level == "高":
                score += 20
            elif level == "中":
                score += 10
            else:
                score += 5
        
        # 检测异常
        anomalies = self.detect_anomaly()
        score += len(anomalies) * 10
        
        # 检查活跃告警
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT alert_level, COUNT(*) 
                    FROM alerts 
                    WHERE is_active = true 
                    AND (end_time IS NULL OR end_time > NOW())
                    GROUP BY alert_level
                """)
                
                for row in cursor.fetchall():
                    level = row[0]
                    count = row[1]
                    if "紧急" in level or level == "CRITICAL":
                        score += count * 15
                    elif "高" in level or level == "HIGH":
                        score += count * 10
                    elif "中" in level or level == "MEDIUM":
                        score += count * 5
                        
        except Exception:
            pass
        
        return min(score, 100)
