"""军事力量结构 - 单位详情页

展示单位完整信息：
- 基本信息（番号、驻地、指挥官、编制员额、装备清单）
- 实时位置（从 positions 表读取）
- 历史轨迹（从 positions 表读取）
- 相关情报（从 intelligence 表读取）
- 预警记录（从 alerts 表读取）
"""
from typing import Dict, List, Optional, Any
from datetime import datetime


class UnitPosition:
    """单位实时位置"""
    
    def __init__(
        self,
        position_id: str,
        unit_id: str,
        position_type: str,  # fixed | moving
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        altitude_m: Optional[str] = None,
        accuracy_m: Optional[str] = None,
        position_source: Optional[str] = None,
        reported_at: Optional[datetime] = None,
    ):
        self.position_id = position_id
        self.unit_id = unit_id
        self.position_type = position_type
        self.latitude = latitude
        self.longitude = longitude
        self.altitude_m = altitude_m
        self.accuracy_m = accuracy_m
        self.position_source = position_source
        self.reported_at = reported_at
    
    def to_dict(self) -> Dict:
        return {
            "position_id": self.position_id,
            "unit_id": self.unit_id,
            "position_type": self.position_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_m": self.altitude_m,
            "accuracy_m": self.accuracy_m,
            "position_source": self.position_source,
            "reported_at": self.reported_at.isoformat() if self.reported_at else None,
        }


class UnitIntel:
    """单位相关情报"""
    
    TYPE_MOVEMENT = "movement"
    TYPE_EXERCISE = "exercise"
    TYPE_DEPLOYMENT = "deployment"
    TYPE_INCIDENT = "incident"
    
    def __init__(
        self,
        intel_id: str,
        title: str,
        intel_type: str,
        content: Optional[str] = None,
        source_reliability: Optional[str] = None,
        credibility: Optional[str] = None,
        location_description: Optional[str] = None,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        event_date: Optional[datetime] = None,
        obtained_date: Optional[datetime] = None,
    ):
        self.intel_id = intel_id
        self.title = title
        self.intel_type = intel_type
        self.content = content
        self.source_reliability = source_reliability
        self.credibility = credibility
        self.location_description = location_description
        self.latitude = latitude
        self.longitude = longitude
        self.event_date = event_date
        self.obtained_date = obtained_date
    
    def to_dict(self) -> Dict:
        return {
            "intel_id": self.intel_id,
            "title": self.title,
            "intel_type": self.intel_type,
            "content": self.content,
            "source_reliability": self.source_reliability,
            "credibility": self.credibility,
            "location_description": self.location_description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "obtained_date": self.obtained_date.isoformat() if self.obtained_date else None,
        }


class UnitAlert:
    """单位预警记录"""
    
    LEVEL_RED = "red"
    LEVEL_ORANGE = "orange"
    LEVEL_YELLOW = "yellow"
    LEVEL_BLUE = "blue"
    
    TYPE_INVASION = "invasion"
    TYPE_AIR_THREAT = "air_threat"
    TYPE_MISSILE = "missile"
    TYPE_OTHER = "other"
    
    def __init__(
        self,
        alert_id: str,
        alert_level: str,
        alert_type: str,
        title: str,
        description: Optional[str] = None,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        affected_area: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        is_active: bool = True,
    ):
        self.alert_id = alert_id
        self.alert_level = alert_level
        self.alert_type = alert_type
        self.title = title
        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.affected_area = affected_area
        self.start_time = start_time
        self.end_time = end_time
        self.is_active = is_active
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "alert_level": self.alert_level,
            "alert_type": self.alert_type,
            "title": self.title,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "affected_area": self.affected_area,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_active": self.is_active,
        }


class UnitDetailView:
    """
    单位详情页视图
    
    整合展示单位的完整信息视图，包含基本信息、位置、情报、预警等。
    
    Usage:
        view = UnitDetailView()
        view.load_unit(unit_id="xxx", unit_data=unit_db_record)
        view.load_positions(positions)  # 从 positions 表
        view.load_intel(intel_records)  # 从 intelligence 表
        view.load_alerts(alert_records)  # 从 alerts 表
        detail = view.get_display_data()  # 供前端渲染
    """
    
    def __init__(self):
        self.unit_id: Optional[str] = None
        self.basic_info: Dict[str, Any] = {}
        self.positions: List[UnitPosition] = []
        self.intel_records: List[UnitIntel] = []
        self.alerts: List[UnitAlert] = []
        self._current_position: Optional[UnitPosition] = None
    
    def load_unit(
        self,
        unit_id: str,
        unit_code: str,
        unit_name: str,
        unit_level: str,
        unit_type: Optional[str] = None,
        country_name: Optional[str] = None,
        branch_name: Optional[str] = None,
        parent_unit_name: Optional[str] = None,
        commander: Optional[str] = None,
        strength: Optional[int] = None,
        location: Optional[Dict] = None,
        is_active: bool = True,
        established_date: Optional[datetime] = None,
    ) -> "UnitDetailView":
        """加载单位基本信息"""
        self.unit_id = unit_id
        self.basic_info = {
            "unit_id": unit_id,
            "unit_code": unit_code,
            "unit_name": unit_name,
            "unit_level": unit_level,
            "unit_type": unit_type,
            "country_name": country_name,
            "branch_name": branch_name,
            "parent_unit_name": parent_unit_name,
            "commander": commander,
            "strength": strength,
            "location": location or {},
            "is_active": is_active,
            "established_date": established_date.isoformat() if established_date else None,
        }
        return self
    
    def load_positions(self, positions: List[Dict]) -> "UnitDetailView":
        """
        加载单位实时位置和历史轨迹
        
        Args:
            positions: 从 positions 表查询的记录列表
        """
        self.positions = []
        for p in positions:
            pos = UnitPosition(
                position_id=p.get("position_id", ""),
                unit_id=p.get("unit_id", ""),
                position_type=p.get("position_type", "fixed"),
                latitude=p.get("latitude"),
                longitude=p.get("longitude"),
                altitude_m=p.get("altitude_m"),
                accuracy_m=p.get("accuracy_m"),
                position_source=p.get("position_source"),
                reported_at=p.get("reported_at"),
            )
            self.positions.append(pos)
        
        # 当前最新位置
        if self.positions:
            self.positions.sort(key=lambda x: x.reported_at or datetime.min, reverse=True)
            self._current_position = self.positions[0]
        
        return self
    
    def load_intel(self, intel_records: List[Dict]) -> "UnitDetailView":
        """加载单位相关情报"""
        self.intel_records = []
        for r in intel_records:
            intel = UnitIntel(
                intel_id=r.get("intel_id", ""),
                title=r.get("title", ""),
                intel_type=r.get("intel_type", ""),
                content=r.get("content"),
                source_reliability=r.get("source_reliability"),
                credibility=r.get("credibility"),
                location_description=r.get("location_description"),
                latitude=r.get("latitude"),
                longitude=r.get("longitude"),
                event_date=r.get("event_date"),
                obtained_date=r.get("obtained_date"),
            )
            self.intel_records.append(intel)
        
        # 按时间倒序
        self.intel_records.sort(
            key=lambda x: x.event_date or datetime.min, reverse=True
        )
        return self
    
    def load_alerts(self, alert_records: List[Dict]) -> "UnitDetailView":
        """加载预警记录"""
        self.alerts = []
        for r in alert_records:
            alert = UnitAlert(
                alert_id=r.get("alert_id", ""),
                alert_level=r.get("alert_level", ""),
                alert_type=r.get("alert_type", ""),
                title=r.get("title", ""),
                description=r.get("description"),
                latitude=r.get("latitude"),
                longitude=r.get("longitude"),
                affected_area=r.get("affected_area"),
                start_time=r.get("start_time"),
                end_time=r.get("end_time"),
                is_active=r.get("is_active", True),
            )
            self.alerts.append(alert)
        
        # 活跃预警优先，按等级排序（红色最紧急）
        level_order = {"red": 0, "orange": 1, "yellow": 2, "blue": 3}
        self.alerts.sort(
            key=lambda x: (
                0 if x.is_active else 1,  # 活跃=0 排前，非活跃=1 排后
                level_order.get(x.alert_level, 99),
                x.start_time or datetime.min,
            ),
            reverse=False,  # False 因为活跃(0)要排前面
        )
        return self
    
    def get_current_position(self) -> Optional[Dict]:
        """获取最新位置"""
        if self._current_position:
            return self._current_position.to_dict()
        return None
    
    def get_position_history(self, limit: int = 100) -> List[Dict]:
        """获取历史轨迹（用于地图轨迹线）"""
        return [p.to_dict() for p in self.positions[:limit]]
    
    def get_active_alerts(self) -> List[Dict]:
        """获取当前活跃预警"""
        return [a.to_dict() for a in self.alerts if a.is_active]
    
    def get_recent_intel(self, limit: int = 20) -> List[Dict]:
        """获取最近情报"""
        return [i.to_dict() for i in self.intel_records[:limit]]
    
    def get_display_data(self) -> Dict:
        """
        获取完整的详情页展示数据
        
        Returns:
            dict: 包含所有信息的详情页数据结构
        """
        return {
            "basic_info": self.basic_info,
            "current_position": self.get_current_position(),
            "position_history": self.get_position_history(),
            "intel": self.get_recent_intel(),
            "alerts": {
                "active": self.get_active_alerts(),
                "all": [a.to_dict() for a in self.alerts],
                "active_count": len([a for a in self.alerts if a.is_active]),
            },
            "stats": {
                "position_count": len(self.positions),
                "intel_count": len(self.intel_records),
                "alert_count": len(self.alerts),
                "active_alert_count": len([a for a in self.alerts if a.is_active]),
            },
        }
    
    def clear(self):
        """清空所有数据"""
        self.unit_id = None
        self.basic_info = {}
        self.positions = []
        self.intel_records = []
        self.alerts = []
        self._current_position = None


def build_unit_detail_from_db(
    unit_db_record: Dict,
    positions: List[Dict],
    intel_records: List[Dict],
    alert_records: List[Dict],
    country_name: Optional[str] = None,
    branch_name: Optional[str] = None,
    parent_unit_name: Optional[str] = None,
) -> Dict:
    """
    从数据库记录构建单位详情页数据
    
    便捷函数，用于一次性构建完整详情页。
    
    Args:
        unit_db_record: units 表记录
        positions: positions 表查询结果
        intel_records: intelligence 表查询结果
        alert_records: alerts 表查询结果
        country_name: 国家名称（JOIN 查询得到）
        branch_name: 军种名称（JOIN 查询得到）
        parent_unit_name: 上级单位名称（JOIN 查询得到）
    
    Returns:
        dict: 完整的详情页数据结构
    """
    view = UnitDetailView()
    view.load_unit(
        unit_id=str(unit_db_record.get("unit_id", "")),
        unit_code=unit_db_record.get("unit_code", ""),
        unit_name=unit_db_record.get("unit_name", ""),
        unit_level=unit_db_record.get("unit_level", ""),
        unit_type=unit_db_record.get("unit_type"),
        country_name=country_name,
        branch_name=branch_name,
        parent_unit_name=parent_unit_name,
        commander=unit_db_record.get("commander"),
        strength=unit_db_record.get("strength"),
        location=unit_db_record.get("location"),
        is_active=unit_db_record.get("is_active", True),
        established_date=unit_db_record.get("established_date"),
    )
    view.load_positions(positions)
    view.load_intel(intel_records)
    view.load_alerts(alert_records)
    return view.get_display_data()