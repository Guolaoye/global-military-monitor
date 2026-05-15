"""军事力量结构 - 单位数据服务层

从 PostgreSQL 数据库读取单位数据，构建树状图/网状图所需的数据结构。
"""
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..db.connection import get_cursor
from .models import TreeViewModel
from ..military_network.models import GraphViewModel
from ..unit_detail.views import UnitDetailView, build_unit_detail_from_db


class UnitService:
    """
    单位数据服务层
    
    负责从数据库加载单位数据，支持：
    - 全量加载（构建树状图）
    - 单个单位详情查询
    - 按国家/军种筛选
    - 台湾地区示例数据录入
    
    Usage:
        service = UnitService()
        tree = service.load_tree_for_country("Taiwan")
        detail = service.get_unit_detail("unit-uuid-xxx")
    """
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Args:
            db_config: 数据库配置，格式为
                {"host": "localhost", "port": 5432, "dbname": "...", "user": "...", "password": "..."}
                若为 None，则从环境变量或 .env 读取
        """
        self.db_config = db_config
    
    def _get_db_params(self) -> Dict[str, Any]:
        """获取数据库连接参数"""
        if self.db_config:
            return self.db_config
        from ..config import load_config
        cfg = load_config()
        return {
            "host": cfg["DB_HOST"],
            "port": cfg["DB_PORT"],
            "dbname": cfg["DB_NAME"],
            "user": cfg["DB_USER"],
            "password": cfg["DB_PASSWORD"],
        }
    
    def load_all_units(self) -> List[Dict]:
        """加载所有单位（带 JOIN 的完整信息）"""
        params = self._get_db_params()
        sql = """
            SELECT 
                u.unit_id, u.unit_code, u.unit_name, u.unit_level, u.unit_type,
                u.is_active, u.established_date, u.dissolved_date,
                u.commander, u.strength, u.garrison_location,
                c.country_id, c.name_zh AS country_name,
                b.branch_id, b.name_zh AS branch_name,
                p.unit_name AS parent_unit_name
            FROM units u
            LEFT JOIN countries c ON u.country_id = c.country_id
            LEFT JOIN military_branches b ON u.branch_id = b.branch_id
            LEFT JOIN units p ON u.parent_unit_id = p.unit_id
            WHERE u.is_active = TRUE
            ORDER BY c.name_zh, b.name_zh, u.unit_level, u.unit_name
        """
        with get_cursor(**params) as cur:
            cur.execute(sql)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    
    def load_units_by_country(self, country_name_or_code: str) -> List[Dict]:
        """按国家名称或代码加载单位"""
        params = self._get_db_params()
        sql = """
            SELECT 
                u.unit_id, u.unit_code, u.unit_name, u.unit_level, u.unit_type,
                u.is_active, u.commander, u.strength, u.garrison_location,
                c.country_id, c.name_zh AS country_name,
                b.branch_id, b.name_zh AS branch_name,
                p.unit_name AS parent_unit_name
            FROM units u
            LEFT JOIN countries c ON u.country_id = c.country_id
            LEFT JOIN military_branches b ON u.branch_id = b.branch_id
            LEFT JOIN units p ON u.parent_unit_id = p.unit_id
            WHERE (c.name_zh = %s OR c.code = %s) AND u.is_active = TRUE
            ORDER BY b.name_zh, u.unit_level, u.unit_name
        """
        with get_cursor(**params) as cur:
            cur.execute(sql, (country_name_or_code, country_name_or_code))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    
    def get_unit_detail(self, unit_id: str) -> Dict:
        """
        获取单位详情页完整数据
        
        Args:
            unit_id: 单位 UUID
        
        Returns:
            dict: 单位详情页数据
        """
        params = self._get_db_params()
        
        # 查询单位基本信息
        unit_sql = """
            SELECT 
                u.unit_id, u.unit_code, u.unit_name, u.unit_level, u.unit_type,
                u.is_active, u.established_date, u.commander, u.strength,
                u.garrison_location,
                c.country_id, c.name_zh AS country_name,
                b.branch_id, b.name_zh AS branch_name,
                p.unit_name AS parent_unit_name
            FROM units u
            LEFT JOIN countries c ON u.country_id = c.country_id
            LEFT JOIN military_branches b ON u.branch_id = b.branch_id
            LEFT JOIN units p ON u.parent_unit_id = p.unit_id
            WHERE u.unit_id = %s
        """
        
        # 查询位置轨迹
        positions_sql = """
            SELECT position_id, unit_id, position_type,
                   latitude, longitude, altitude_m, accuracy_m,
                   position_source, reported_at
            FROM positions
            WHERE unit_id = %s
            ORDER BY reported_at DESC
            LIMIT 100
        """
        
        # 查询相关情报
        intel_sql = """
            SELECT intel_id, intel_type, title, content,
                   source_reliability, credibility,
                   location_description, latitude, longitude,
                   event_date, obtained_date
            FROM intelligence
            WHERE country_id = (
                SELECT country_id FROM units WHERE unit_id = %s
            )
            ORDER BY event_date DESC
            LIMIT 20
        """
        
        # 查询预警记录
        alerts_sql = """
            SELECT alert_id, alert_level, alert_type, title, description,
                   latitude, longitude, affected_area,
                   start_time, end_time, is_active
            FROM alerts
            WHERE country_id = (
                SELECT country_id FROM units WHERE unit_id = %s
            )
            ORDER BY is_active DESC, start_time DESC
        """
        
        with get_cursor(**params) as cur:
            # 单位基本信息
            cur.execute(unit_sql, (unit_id,))
            cols = [desc[0] for desc in cur.description]
            unit_record = cur.fetchone()
            if not unit_record:
                return {"error": f"单位 {unit_id} 不存在"}
            unit_record = dict(zip(cols, unit_record))
            
            country_id_for_intel = unit_record.get("country_id")
            
            # 位置轨迹
            cur.execute(positions_sql, (unit_id,))
            cols = [desc[0] for desc in cur.description]
            positions = [dict(zip(cols, row)) for row in cur.fetchall()]
            
            # 情报
            cur.execute(intel_sql, (unit_id,))
            cols = [desc[0] for desc in cur.description]
            intel_records = [dict(zip(cols, row)) for row in cur.fetchall()]
            
            # 预警
            cur.execute(alerts_sql, (unit_id,))
            cols = [desc[0] for desc in cur.description]
            alerts = [dict(zip(cols, row)) for row in cur.fetchall()]
        
        return build_unit_detail_from_db(
            unit_record, positions, intel_records, alerts,
            country_name=unit_record.get("country_name"),
            branch_name=unit_record.get("branch_name"),
            parent_unit_name=unit_record.get("parent_unit_name"),
        )
    
    def build_tree_model(
        self,
        units: Optional[List[Dict]] = None,
        country_name: Optional[str] = None,
    ) -> TreeViewModel:
        """
        构建树状图模型
        
        Args:
            units: 单位数据列表，若为 None 则从数据库加载
            country_name: 若指定，则只加载该国家的单位
        
        Returns:
            TreeViewModel: 已构建好的树状图模型
        """
        if units is None:
            if country_name:
                units = self.load_units_by_country(country_name)
            else:
                units = self.load_all_units()
        
        tree = TreeViewModel()
        
        # 按国家分组
        country_map: Dict[str, Dict] = {}
        branch_map: Dict[str, Dict] = {}
        
        for unit in units:
            country_id = unit.get("country_id")
            branch_id = unit.get("branch_id")
            unit_id = str(unit.get("unit_id", ""))
            
            # 确保国家节点存在
            if country_id and country_id not in country_map:
                country_map[country_id] = tree.add_country(
                    country_id=country_id,
                    name_zh=unit.get("country_name", "未知"),
                )
            
            # 确保军种节点存在
            if branch_id and branch_id not in branch_map:
                branch_node = tree.add_branch(
                    branch_id=branch_id,
                    country_id=country_id,
                    name_zh=unit.get("branch_name", "未知军种"),
                    branch_type=unit.get("branch_type"),
                )
                if branch_node:
                    branch_map[branch_id] = branch_node
            
            # 添加单位节点
            parent_id = str(unit.get("parent_unit_id") or branch_id or country_id)
            unit_node = tree.add_unit(
                unit_id=unit_id,
                parent_id=parent_id,
                unit_name=unit.get("unit_name", ""),
                unit_level=unit.get("unit_level", ""),
                unit_code=unit.get("unit_code"),
                unit_type=unit.get("unit_type"),
                commander=unit.get("commander"),
                strength=unit.get("strength"),
                location=unit.get("garrison_location"),
            )
        
        return tree
    
    def build_graph_model(
        self,
        tree_model: Optional[TreeViewModel] = None,
        country_name: Optional[str] = None,
    ) -> GraphViewModel:
        """
        构建网状图模型
        
        Args:
            tree_model: 若提供，则从树状图加载；否则从数据库加载
            country_name: 若指定，则只加载该国家的单位
        
        Returns:
            GraphViewModel: 已构建好的网状图模型
        """
        graph = GraphViewModel()
        
        if tree_model is None:
            tree_model = self.build_tree_model(country_name=country_name)
        
        graph.load_from_tree(tree_model)
        graph.force_directed_layout(iterations=50)
        
        return graph
    
    def load_equipment_for_unit(self, unit_id: str) -> List[Dict]:
        """加载单位装备清单"""
        params = self._get_db_params()
        sql = """
            SELECT equipment_id, equipment_type, equipment_name,
                   model_code, manufacturer, specifications,
                   operational_status, inventory_count,
                   deployment_location, first_service_date
            FROM equipment
            WHERE unit_id = %s
            ORDER BY equipment_type, equipment_name
        """
        with get_cursor(**params) as cur:
            cur.execute(sql, (unit_id,))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    
    def get_subordinate_units(self, unit_id: str) -> List[Dict]:
        """获取下级单位列表"""
        params = self._get_db_params()
        sql = """
            SELECT unit_id, unit_code, unit_name, unit_level, unit_type,
                   commander, strength
            FROM units
            WHERE parent_unit_id = %s AND is_active = TRUE
            ORDER BY unit_level, unit_name
        """
        with get_cursor(**params) as cur:
            cur.execute(sql, (unit_id,))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    
    def search_units(self, keyword: str, country_name: Optional[str] = None) -> List[Dict]:
        """搜索单位"""
        params = self._get_db_params()
        
        if country_name:
            sql = """
                SELECT u.unit_id, u.unit_code, u.unit_name, u.unit_level, u.unit_type,
                       c.name_zh AS country_name, b.name_zh AS branch_name
                FROM units u
                LEFT JOIN countries c ON u.country_id = c.country_id
                LEFT JOIN military_branches b ON u.branch_id = b.branch_id
                WHERE (u.unit_name LIKE %s OR u.unit_code LIKE %s)
                  AND c.name_zh = %s
                LIMIT 50
            """
            pattern = f"%{keyword}%"
            with get_cursor(**params) as cur:
                cur.execute(sql, (pattern, pattern, country_name))
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        else:
            sql = """
                SELECT u.unit_id, u.unit_code, u.unit_name, u.unit_level, u.unit_type,
                       c.name_zh AS country_name, b.name_zh AS branch_name
                FROM units u
                LEFT JOIN countries c ON u.country_id = c.country_id
                LEFT JOIN military_branches b ON u.branch_id = b.branch_id
                WHERE u.unit_name LIKE %s OR u.unit_code LIKE %s
                LIMIT 50
            """
            pattern = f"%{keyword}%"
            with get_cursor(**params) as cur:
                cur.execute(sql, (pattern, pattern))
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]


class TaiwanDataSeeder:
    """
    台湾地区军事编制示例数据录入器
    
    按项目规范书 3.3.3 节要求录入台湾地区编制数据：
    - 台中守备区 → 第十军团 → 各旅
    - 第九军团、第八军团、台北守备区、台南守备区
    - 第58炮兵指挥部、第36化学兵旅、第52工兵群
    """
    
    # 台湾地区编制数据（示例）
    TAIWAN_DATA = {
        "country": {
            "code": "TWN",
            "name_zh": "台湾地区",
            "region": "东亚",
        },
        "branches": [
            {"code": "TW_ARMY", "name_zh": "陆军", "branch_type": "army"},
            {"code": "TW_NAVY", "name_zh": "海军", "branch_type": "navy"},
            {"code": "TW_AIR", "name_zh": "空军", "branch_type": "air_force"},
        ],
        "units": [
            # 台北守备区
            {
                "unit_code": "TWN-CMD-TH",
                "unit_name": "台北防卫指挥部",
                "unit_level": "指挥部",
                "unit_type": "defense_command",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 20000,
                "location": {"name": "台北市", "latitude": "25.0330", "longitude": "121.5654"},
            },
            # 台中守备区
            {
                "unit_code": "TWN-CMD-TCC",
                "unit_name": "台中防卫指挥部",
                "unit_level": "指挥部",
                "unit_type": "defense_command",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 25000,
                "location": {"name": "台中市", "latitude": "24.1477", "longitude": "120.6736"},
            },
            # 台南守备区
            {
                "unit_code": "TWN-CMD-TN",
                "unit_name": "台南防卫指挥部",
                "unit_level": "指挥部",
                "unit_type": "defense_command",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 18000,
                "location": {"name": "台南市", "latitude": "22.9998", "longitude": "120.2269"},
            },
            # 第六军团（桃园）
            {
                "unit_code": "TWN-ARMY-6COR",
                "unit_name": "第六军团",
                "unit_level": "军团",
                "unit_type": "corps",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 30000,
                "location": {"name": "桃园市", "latitude": "24.9936", "longitude": "121.3010"},
            },
            # 第八军团（高雄）
            {
                "unit_code": "TWN-ARMY-8COR",
                "unit_name": "第八军团",
                "unit_level": "军团",
                "unit_type": "corps",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 35000,
                "location": {"name": "高雄市", "latitude": "22.6273", "longitude": "120.3014"},
            },
            # 第九军团（花莲）
            {
                "unit_code": "TWN-ARMY-9COR",
                "unit_name": "第九军团",
                "unit_level": "军团",
                "unit_type": "corps",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 25000,
                "location": {"name": "花莲县", "latitude": "23.9875", "longitude": "121.6011"},
            },
            # 第十军团（台中）
            {
                "unit_code": "TWN-ARMY-10COR",
                "unit_name": "第十军团",
                "unit_level": "军团",
                "unit_type": "corps",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 30000,
                "location": {"name": "台中市", "latitude": "24.1477", "longitude": "120.6736"},
            },
            # 陆军总部
            {
                "unit_code": "TWN-ARMY-HQ",
                "unit_name": "陆军司令部",
                "unit_level": "总部",
                "unit_type": "headquarters",
                "parent_code": None,
                "commander": None,
                "strength": None,
                "location": {"name": "台北市", "latitude": "25.0330", "longitude": "121.5654"},
            },
            # 第58炮兵指挥部
            {
                "unit_code": "TWN-ARTY-58",
                "unit_name": "第五十八炮兵指挥部",
                "unit_level": "指挥部",
                "unit_type": "artillery",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 5000,
                "location": {"name": "屏东县", "latitude": "22.5519", "longitude": "120.5487"},
            },
            # 第36化学兵旅
            {
                "unit_code": "TWN-CBRN-36",
                "unit_name": "第三十六化学兵旅",
                "unit_level": "旅",
                "unit_type": "cbrn",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 3000,
                "location": {"name": "桃园市", "latitude": "24.9936", "longitude": "121.3010"},
            },
            # 第52工兵群
            {
                "unit_code": "TWN-ENG-52",
                "unit_name": "第五十二工兵群",
                "unit_level": "群",
                "unit_type": "engineer",
                "parent_code": "TWN-ARMY-HQ",
                "commander": None,
                "strength": 2500,
                "location": {"name": "台南市", "latitude": "22.9998", "longitude": "120.2269"},
            },
        ],
    }
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config
    
    def _get_db_params(self) -> Dict[str, Any]:
        if self.db_config:
            return self.db_config
        from ..config import load_config
        cfg = load_config()
        return {
            "host": cfg["DB_HOST"],
            "port": cfg["DB_PORT"],
            "dbname": cfg["DB_NAME"],
            "user": cfg["DB_USER"],
            "password": cfg["DB_PASSWORD"],
        }
    
    def seed(self) -> Dict[str, Any]:
        """
        执行台湾地区示例数据录入
        
        Returns:
            dict: 录入结果统计
        """
        params = self._get_db_params()
        data = self.TAIWAN_DATA
        stats = {"countries_created": 0, "branches_created": 0, "units_created": 0, "errors": []}
        
        with get_cursor(**params) as cur:
            # 1. 插入/更新国家
            country_sql = """
                INSERT INTO countries (country_id, code, name_zh, region)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name_zh = EXCLUDED.name_zh,
                    region = EXCLUDED.region
                RETURNING country_id
            """
            country_uuid = str(uuid.uuid4())
            try:
                cur.execute(country_sql, (
                    country_uuid,
                    data["country"]["code"],
                    data["country"]["name_zh"],
                    data["country"]["region"],
                ))
                result = cur.fetchone()
                country_id = str(result[0]) if result else None
                if country_id:
                    stats["countries_created"] += 1
            except Exception as e:
                stats["errors"].append(f"国家插入失败: {e}")
                return stats
            
            # 2. 插入军种
            branch_ids = {}
            for branch in data["branches"]:
                branch_sql = """
                    INSERT INTO military_branches (branch_id, country_id, code, name_zh, branch_type)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (code) DO UPDATE SET
                        name_zh = EXCLUDED.name_zh,
                        branch_type = EXCLUDED.branch_type
                    RETURNING branch_id
                """
                branch_uuid = str(uuid.uuid4())
                try:
                    cur.execute(branch_sql, (
                        branch_uuid,
                        country_id,
                        branch["code"],
                        branch["name_zh"],
                        branch["branch_type"],
                    ))
                    result = cur.fetchone()
                    branch_ids[branch["code"]] = str(result[0]) if result else None
                    if result:
                        stats["branches_created"] += 1
                except Exception as e:
                    stats["errors"].append(f"军种 {branch['code']} 插入失败: {e}")
            
            # 3. 插入单位（分两批：先插总部，再插其他）
            army_branch_id = branch_ids.get("TW_ARMY")
            
            # 先插入陆军总部（无父单位）
            army_hq_unit = next((u for u in data["units"] if u["unit_code"] == "TWN-ARMY-HQ"), None)
            if army_hq_unit:
                unit_sql = """
                    INSERT INTO units (
                        unit_id, country_id, branch_id, parent_unit_id,
                        unit_code, unit_name, unit_level, unit_type,
                        commander, strength, garrison_location
                    )
                    VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (unit_code) DO UPDATE SET
                        unit_name = EXCLUDED.unit_name,
                        unit_level = EXCLUDED.unit_level,
                        commander = EXCLUDED.commander,
                        strength = EXCLUDED.strength
                    RETURNING unit_id
                """
                unit_uuid = str(uuid.uuid4())
                try:
                    cur.execute(unit_sql, (
                        unit_uuid,
                        country_id,
                        army_branch_id,
                        army_hq_unit["unit_code"],
                        army_hq_unit["unit_name"],
                        army_hq_unit["unit_level"],
                        army_hq_unit["unit_type"],
                        army_hq_unit.get("commander"),
                        army_hq_unit.get("strength"),
                        str(army_hq_unit.get("location", {})),
                    ))
                    result = cur.fetchone()
                    if result:
                        branch_ids["TWN-ARMY-HQ"] = str(result[0])
                        stats["units_created"] += 1
                except Exception as e:
                    stats["errors"].append(f"单位 {army_hq_unit['unit_code']} 插入失败: {e}")
            
            # 插入其余单位
            for unit in data["units"]:
                if unit["unit_code"] == "TWN-ARMY-HQ":
                    continue
                
                parent_id = branch_ids.get(unit.get("parent_code"))
                
                unit_sql = """
                    INSERT INTO units (
                        unit_id, country_id, branch_id, parent_unit_id,
                        unit_code, unit_name, unit_level, unit_type,
                        commander, strength, garrison_location
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (unit_code) DO UPDATE SET
                        unit_name = EXCLUDED.unit_name,
                        unit_level = EXCLUDED.unit_level,
                        commander = EXCLUDED.commander,
                        strength = EXCLUDED.strength
                    RETURNING unit_id
                """
                unit_uuid = str(uuid.uuid4())
                try:
                    cur.execute(unit_sql, (
                        unit_uuid,
                        country_id,
                        army_branch_id,
                        parent_id,
                        unit["unit_code"],
                        unit["unit_name"],
                        unit["unit_level"],
                        unit["unit_type"],
                        unit.get("commander"),
                        unit.get("strength"),
                        str(unit.get("location", {})),
                    ))
                    if cur.fetchone():
                        stats["units_created"] += 1
                except Exception as e:
                    stats["errors"].append(f"单位 {unit['unit_code']} 插入失败: {e}")
        
        return stats
    
    def get_data_json(self) -> Dict:
        """返回台湾地区示例数据（供直接使用，不入库）"""
        return self.TAIWAN_DATA
