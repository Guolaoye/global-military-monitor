"""军事力量结构模块测试

测试树状图、网状图、单位详情页功能。
"""
import pytest
import json
import uuid
from datetime import datetime

from src.military_tree.models import TreeViewModel, TreeNode
from src.military_network.models import GraphViewModel, GraphEdge
from src.unit_detail.views import (
    UnitDetailView, UnitPosition, UnitIntel, UnitAlert,
    build_unit_detail_from_db
)


class TestTreeViewModel:
    """树状图模型测试"""
    
    def test_add_country(self):
        tree = TreeViewModel()
        country = tree.add_country("twn", "台湾地区", region="东亚")
        
        assert country.node_id == "twn"
        assert country.name == "台湾地区"
        assert country.node_type == "country"
        assert country.level == 1
    
    def test_add_branch(self):
        tree = TreeViewModel()
        tree.add_country("twn", "台湾地区")
        branch = tree.add_branch("army", "twn", "陆军", branch_type="army")
        
        assert branch is not None
        assert branch.node_id == "army"
        assert branch.name == "陆军"
        assert branch.level == 2
    
    def test_add_unit(self):
        tree = TreeViewModel()
        tree.add_country("twn", "台湾地区")
        tree.add_branch("army", "twn", "陆军", branch_type="army")
        unit = tree.add_unit(
            "10cor", "army", "第十军团",
            unit_level="军团", unit_code="TWN-10COR"
        )
        
        assert unit is not None
        assert unit.node_id == "10cor"
        assert unit.name == "第十军团"
        assert unit.level == 3
    
    def test_tree_hierarchy(self):
        tree = TreeViewModel()
        tree.add_country("twn", "台湾地区")
        tree.add_branch("army", "twn", "陆军", branch_type="army")
        tree.add_unit("10cor", "army", "第十军团", "军团")
        tree.add_unit("58arty", "10cor", "第58炮兵指挥部", "指挥部")
        
        # 验证父子关系
        army_node = tree.get_node("army")
        assert len(army_node.children) == 1
        assert army_node.children[0].node_id == "10cor"
        
        # 验证层级
        cor_node = tree.get_node("10cor")
        assert cor_node.children[0].node_id == "58arty"
        assert cor_node.children[0].level == 4
    
    def test_expand_collapse(self):
        tree = TreeViewModel()
        tree.add_country("twn", "台湾地区")
        
        node = tree.get_node("twn")
        assert node.is_expanded is True  # 默认展开
        
        tree.collapse("twn")
        assert node.is_expanded is False
        
        tree.toggle("twn")
        assert node.is_expanded is True
    
    def test_search(self):
        tree = TreeViewModel()
        tree.add_country("twn", "台湾地区")
        tree.add_branch("army", "twn", "陆军", branch_type="army")
        tree.add_unit("10cor", "army", "第十军团", "军团")
        
        results = tree.search("军团")
        assert len(results) == 1
        assert results[0]["name"] == "第十军团"
    
    def test_get_tree_json(self):
        tree = TreeViewModel()
        tree.add_country("twn", "台湾地区")
        tree.add_branch("army", "twn", "陆军", branch_type="army")
        
        json_data = tree.get_tree_json()
        assert json_data["id"] == TreeViewModel.ROOT_ID
        assert len(json_data["children"]) == 1
        assert json_data["children"][0]["name"] == "台湾地区"
    
    def test_add_equipment(self):
        tree = TreeViewModel()
        tree.add_country("twn", "台湾地区")
        tree.add_branch("army", "twn", "陆军", branch_type="army")
        tree.add_unit("10cor", "army", "第十军团", "军团")
        
        result = tree.add_equipment(
            "10cor", "eq-001", "M1坦克",
            model_code="M1", equipment_type="tank",
            inventory_count=100
        )
        
        assert result is True
        unit_node = tree.get_node("10cor")
        assert "equipment" in unit_node.data
        assert len(unit_node.data["equipment"]) == 1
        assert unit_node.data["equipment"][0]["name"] == "M1坦克"
    
    def test_stats(self):
        tree = TreeViewModel()
        tree.add_country("twn", "台湾地区")
        tree.add_branch("army", "twn", "陆军", branch_type="army")
        tree.add_branch("navy", "twn", "海军", branch_type="navy")
        tree.add_unit("10cor", "army", "第十军团", "军团")
        tree.add_unit("8cor", "army", "第八军团", "军团")
        
        stats = tree.get_stats()
        assert stats["countries"] == 1
        assert stats["branches"] == 2
        assert stats["units"] == 2


class TestGraphViewModel:
    """网状图模型测试"""
    
    def test_add_node(self):
        graph = GraphViewModel()
        node = graph.add_node("unit-001", "第十军团", "unit")
        
        assert node.node_id == "unit-001"
        assert node.name == "第十军团"
        assert "unit-001" in graph.nodes
    
    def test_add_edge(self):
        graph = GraphViewModel()
        graph.add_node("unit-001", "第十军团")
        graph.add_node("unit-002", "第八军团")
        result = graph.add_edge("unit-001", "unit-002", "command")
        
        assert result is True
        assert len(graph.edges) == 1
        assert "unit-002" in graph.nodes["unit-001"].get_connections()
    
    def test_get_neighbors(self):
        graph = GraphViewModel()
        graph.add_node("unit-001", "第十军团")
        graph.add_node("unit-002", "第八军团")
        graph.add_node("unit-003", "海军")
        graph.add_edge("unit-001", "unit-002", "command")
        
        neighbors = graph.get_neighbors("unit-001")
        assert "unit-002" in neighbors
    
    def test_force_directed_layout(self):
        graph = GraphViewModel()
        for i in range(5):
            graph.add_node(f"unit-{i}", f"单位{i}")
        
        graph.add_edge("unit-0", "unit-1")
        graph.add_edge("unit-1", "unit-2")
        graph.add_edge("unit-2", "unit-3")
        
        graph.force_directed_layout(iterations=10)
        
        # 验证节点位置已更新（不全为0）
        for i in range(5):
            node = graph.nodes[f"unit-{i}"]
            # 至少有一个节点位置不为初始值
            if i > 0:
                assert node.x != 0.0 or node.y != 0.0 or i == 0
    
    def test_get_graph_json(self):
        graph = GraphViewModel()
        graph.add_node("unit-001", "第十军团", "unit")
        graph.add_node("unit-002", "第八军团", "unit")
        graph.add_edge("unit-001", "unit-002", "command")
        
        json_data = graph.get_graph_json()
        assert json_data["stats"]["node_count"] == 2
        assert json_data["stats"]["edge_count"] == 1
    
    def test_search_nodes(self):
        graph = GraphViewModel()
        graph.add_node("unit-001", "第十军团")
        graph.add_node("unit-002", "第八军团")
        
        results = graph.search_nodes("军团")
        assert len(results) == 2
    
    def test_clear(self):
        graph = GraphViewModel()
        graph.add_node("unit-001", "第十军团")
        graph.add_edge("unit-001", "unit-002", "command")
        
        graph.clear()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0


class TestUnitDetailView:
    """单位详情页测试"""
    
    def test_load_unit(self):
        view = UnitDetailView()
        view.load_unit(
            unit_id="unit-001",
            unit_code="TWN-10COR",
            unit_name="第十军团",
            unit_level="军团",
            unit_type="corps",
            country_name="台湾地区",
            branch_name="陆军",
            commander="张三",
            strength=30000,
        )
        
        assert view.unit_id == "unit-001"
        assert view.basic_info["unit_name"] == "第十军团"
        assert view.basic_info["commander"] == "张三"
        assert view.basic_info["strength"] == 30000
    
    def test_load_positions(self):
        view = UnitDetailView()
        positions = [
            {
                "position_id": "pos-001",
                "unit_id": "unit-001",
                "position_type": "fixed",
                "latitude": "24.1477",
                "longitude": "120.6736",
                "reported_at": datetime(2026, 5, 15, 10, 0, 0),
            },
            {
                "position_id": "pos-002",
                "unit_id": "unit-001",
                "position_type": "fixed",
                "latitude": "24.1478",
                "longitude": "120.6737",
                "reported_at": datetime(2026, 5, 14, 10, 0, 0),
            },
        ]
        view.load_positions(positions)
        
        assert len(view.positions) == 2
        # 最新位置应该在第一个
        assert view.positions[0].position_id == "pos-001"
        assert view._current_position.latitude == "24.1477"
    
    def test_load_intel(self):
        view = UnitDetailView()
        intel_records = [
            {
                "intel_id": "intel-001",
                "title": "演习情报",
                "intel_type": "exercise",
                "content": "第十军团在台中举行演习",
                "event_date": datetime(2026, 5, 10),
            },
        ]
        view.load_intel(intel_records)
        
        assert len(view.intel_records) == 1
        assert view.intel_records[0].title == "演习情报"
    
    def test_load_alerts(self):
        view = UnitDetailView()
        alerts = [
            {
                "alert_id": "alert-001",
                "alert_level": "orange",
                "alert_type": "air_threat",
                "title": "空中威胁预警",
                "is_active": True,
                "start_time": datetime(2026, 5, 15),
            },
            {
                "alert_id": "alert-002",
                "alert_level": "yellow",
                "alert_type": "other",
                "title": "一般预警",
                "is_active": False,
                "start_time": datetime(2026, 5, 10),
            },
        ]
        view.load_alerts(alerts)
        
        assert len(view.alerts) == 2
        # 活跃预警应该在前面
        assert view.alerts[0].is_active is True
        assert view.alerts[0].alert_level == "orange"
    
    def test_get_display_data(self):
        view = UnitDetailView()
        view.load_unit(
            unit_id="unit-001",
            unit_code="TWN-10COR",
            unit_name="第十军团",
            unit_level="军团",
            strength=30000,
        )
        view.load_positions([
            {
                "position_id": "pos-001",
                "unit_id": "unit-001",
                "position_type": "fixed",
                "latitude": "24.1477",
                "longitude": "120.6736",
                "reported_at": datetime(2026, 5, 15, 10, 0, 0),
            }
        ])
        
        display = view.get_display_data()
        
        assert "basic_info" in display
        assert "current_position" in display
        assert "stats" in display
        assert display["stats"]["position_count"] == 1


class TestBuildUnitDetailFromDb:
    """从DB记录构建详情页测试"""
    
    def test_basic_construction(self):
        unit_record = {
            "unit_id": uuid.uuid4(),
            "unit_code": "TWN-10COR",
            "unit_name": "第十军团",
            "unit_level": "军团",
            "unit_type": "corps",
            "is_active": True,
            "commander": "张三",
            "strength": 30000,
        }
        
        result = build_unit_detail_from_db(
            unit_db_record=unit_record,
            positions=[],
            intel_records=[],
            alert_records=[],
            country_name="台湾地区",
            branch_name="陆军",
        )
        
        assert result["basic_info"]["unit_name"] == "第十军团"
        assert result["basic_info"]["commander"] == "张三"
        assert result["basic_info"]["country_name"] == "台湾地区"


class TestTaiwanDataSeeder:
    """台湾数据录入测试（数据结构验证）"""
    
    def test_taiwan_data_structure(self):
        """验证台湾示例数据的JSON结构正确"""
        data_path = "data/taiwan_units.json"
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "country" in data
        assert "branches" in data
        assert "units" in data
        
        # 验证国家
        assert data["country"]["code"] == "TWN"
        assert data["country"]["name_zh"] == "台湾地区"
        
        # 验证军种
        branch_codes = [b["code"] for b in data["branches"]]
        assert "TW_ARMY" in branch_codes
        assert "TW_NAVY" in branch_codes
        assert "TW_AIR" in branch_codes
        
        # 验证单位数量
        assert len(data["units"]) == 11
        
        # 验证必须包含规范书要求的单位
        unit_codes = [u["unit_code"] for u in data["units"]]
        assert "TWN-ARMY-10COR" in unit_codes  # 第十军团
        assert "TWN-ARMY-9COR" in unit_codes   # 第九军团
        assert "TWN-ARMY-8COR" in unit_codes   # 第八军团
        assert "TWN-CMD-TCC" in unit_codes     # 台中守备区
        assert "TWN-CMD-TH" in unit_codes     # 台北守备区
        assert "TWN-CMD-TN" in unit_codes     # 台南守备区
        assert "TWN-ARTY-58" in unit_codes    # 第58炮兵指挥部
        assert "TWN-CBRN-36" in unit_codes    # 第36化学兵旅
        assert "TWN-ENG-52" in unit_codes     # 第52工兵群
        
        # 验证指挥关系
        assert "command_relations" in data
        relations = data["command_relations"]
        assert len(relations) > 0
        
        # 陆军总部应为所有单位的上级
        army_hq_relations = [r for r in relations if r["source"] == "TWN-ARMY-HQ"]
        assert len(army_hq_relations) >= 9  # 至少9个子单位


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
