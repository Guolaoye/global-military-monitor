import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.connection import get_cursor
from src.db.models import Alert
from src.threat_alert.rules import ALL_RULES, AlertLevel
from src.threat_alert.feishu_notifier import FeishuNotifier
from src.threat_alert.analyzer import ThreatAnalyzer


class ThreatAlertManager:
    """威胁告警管理器"""
    
    def __init__(self):
        self.notifier = FeishuNotifier()
        self.analyzer = ThreatAnalyzer()
    
    def check_and_alert(self) -> List[Dict[str, Any]]:
        """运行所有告警规则并发送通知"""
        triggered = []
        
        detection_results = self.auto_detect()
        for result in detection_results:
            level = result.get("level", "中")
            title = result.get("title", "未知告警")
            description = result.get("description", "")
            intel_id = result.get("intel_id")
            
            alert = self.add_alert(level, title, description, intel_id)
            if alert:
                triggered.append(alert)
                
                self.notifier.send_alert({
                    "level": level,
                    "title": title,
                    "description": description,
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude")
                })
        
        return triggered
    
    def add_alert(
        self,
        level: str,
        title: str,
        description: str,
        intel_id: Optional[int] = None,
        country_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """添加告警到数据库"""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alerts (
                        alert_level, alert_type, title, description,
                        source_intel_id, country_id, latitude, longitude,
                        is_active, start_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true, NOW())
                    RETURNING id, alert_level, title, description, 
                              latitude, longitude, start_time
                """, (
                    level, self._get_alert_type(level),
                    title, description, intel_id, country_id,
                    latitude, longitude
                ))
                
                row = cursor.fetchone()
                return {
                    "id": row[0],
                    "level": row[1],
                    "title": row[2],
                    "description": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "start_time": row[6].isoformat() if row[6] else None
                }
                
        except Exception as e:
            print(f"[ThreatAlertManager] 添加告警失败: {e}")
            return None
    
    def _get_alert_type(self, level: str) -> str:
        """根据级别获取告警类型"""
        type_map = {
            "紧急": "war_imminent",
            "高": "power_reversal",
            "中": "strategic_change",
            "低": "conflict_ending"
        }
        return type_map.get(level, "general")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取所有活跃告警"""
        alerts = []
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, alert_level, alert_type, title, description,
                           source_intel_id, country_id, latitude, longitude,
                           start_time, end_time
                    FROM alerts
                    WHERE is_active = true
                    AND (end_time IS NULL OR end_time > NOW())
                    ORDER BY 
                        CASE alert_level
                            WHEN 紧急 THEN 1
                            WHEN 高 THEN 2
                            WHEN 中 THEN 3
                            WHEN 低 THEN 4
                        END,
                        start_time DESC
                """)
                
                for row in cursor.fetchall():
                    alerts.append({
                        "id": row[0],
                        "level": row[1],
                        "type": row[2],
                        "title": row[3],
                        "description": row[4],
                        "intel_id": row[5],
                        "country_id": row[6],
                        "latitude": row[7],
                        "longitude": row[8],
                        "start_time": row[9].isoformat() if row[9] else None,
                        "end_time": row[10].isoformat() if row[10] else None
                    })
                    
        except Exception as e:
            print(f"[ThreatAlertManager] 获取告警失败: {e}")
        
        return alerts
    
    def resolve_alert(self, alert_id: int) -> bool:
        """标记告警为已解决"""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    UPDATE alerts
                    SET is_active = false, end_time = NOW()
                    WHERE id = %s
                """, (alert_id,))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"[ThreatAlertManager] 解决告警失败: {e}")
            return False
    
    def auto_detect(self) -> List[Dict[str, Any]]:
        """自动检测分析Intelligence表中的模式"""
        results = []
        
        trends = self.analyzer.analyze_intelligence_trends()
        for trend in trends:
            level = trend.get("level", "中")
            title = f"自动检测: {trend.get(type, 未知类型)}"
            description = trend.get("text", trend.get("detail", "自动分析发现异常"))
            
            results.append({
                "level": level,
                "title": title,
                "description": description,
                "intel_id": trend.get("intel_id"),
                "latitude": trend.get("latitude"),
                "longitude": trend.get("longitude")
            })
        
        anomalies = self.analyzer.detect_anomaly()
        for anomaly in anomalies:
            results.append({
                "level": anomaly.get("level", "高"),
                "title": f"异常检测: {anomaly.get(type, 统计异常)}",
                "description": anomaly.get("detail", ""),
                "intel_id": None
            })
        
        return results
