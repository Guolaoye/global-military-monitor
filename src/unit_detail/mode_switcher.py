"""军事力量结构视图模式切换器

支持在以下模式之间切换：
- tree: 树状图（层级：国家→军种→部队→营/连）
- network: 网状图（单位间关系线）

Usage:
    switcher = ViewModeSwitcher()
    switcher.load_tree_data(units_data)
    switcher.load_network_data(units_data)
    
    # 切换到树状图模式
    switcher.set_mode("tree")
    tree_json = switcher.get_current_view()
    
    # 切换到网状图模式
    switcher.set_mode("network")
    network_json = switcher.get_current_view()
"""
from typing import Dict, List, Optional, Any, Literal

from ..military_tree.models import TreeViewModel
from ..military_network.models import GraphViewModel


class ViewModeSwitcher:
    """
    树状图 / 网状图 模式切换器
    
    同时维护 TreeViewModel 和 GraphViewModel 实例，
    按需导出对应 JSON 数据供前端渲染。
    """

    MODE_TREE = "tree"
    MODE_NETWORK = "network"

    def __init__(self):
        self._mode: Literal["tree", "network"] = self.MODE_TREE
        self._tree_model = TreeViewModel()
        self._network_model = GraphViewModel()
        self._data_loaded = False

    @property
    def current_mode(self) -> str:
        """当前模式"""
        return self._mode

    def set_mode(self, mode: Literal["tree", "network"]) -> bool:
        """
        切换视图模式
        
        Args:
            mode: "tree" 或 "network"
        
        Returns:
            bool: 切换是否成功
        """
        if mode not in (self.MODE_TREE, self.MODE_NETWORK):
            return False
        self._mode = mode
        return True

    def toggle_mode(self) -> str:
        """
        切换到另一种模式
        
        Returns:
            str: 切换后的模式
        """
        self._mode = self.MODE_NETWORK if self._mode == self.MODE_TREE else self.MODE_TREE
        return self._mode

    # ── 数据加载 ────────────────────────────────────────────────

    def load_from_units(self, units: List[Dict]) -> "ViewModeSwitcher":
        """
        从单位列表同时构建树状图和网状图数据
        
        Args:
            units: 单位数据列表，每项包含:
                unit_id, unit_code, unit_name, unit_level, unit_type,
                country_name, branch_name, parent_unit_id, commander,
                strength, location, equipment
        """
        self._tree_model = TreeViewModel()
        self._network_model = GraphViewModel()
        country_nodes: Dict[str, Any] = {}
        branch_nodes: Dict[str, Any] = {}

        for unit in units:
            country_name = unit.get("country_name", "未知国家")
            branch_name = unit.get("branch_name", "未知军种")
            unit_id = unit.get("unit_id", "")
            parent_unit_id = unit.get("parent_unit_id")
            location = unit.get("location") or {}

            # ── 树状图：逐级添加节点 ──
            # 国家节点
            if country_name not in country_nodes:
                country_node = self._tree_model.add_country(
                    country_id=f"country-{country_name}",
                    name_zh=country_name,
                )
                country_nodes[country_name] = country_node.node_id

            # 军种节点（挂在国家下）
            branch_key = f"{country_name}-{branch_name}"
            if branch_key not in branch_nodes:
                branch_node = self._tree_model.add_branch(
                    branch_id=f"branch-{branch_key}",
                    country_id=country_nodes[country_name],
                    name_zh=branch_name,
                )
                branch_nodes[branch_key] = branch_node.node_id if branch_node else None

            branch_id = branch_nodes.get(branch_key)
            parent_id = branch_id

            # 营/连级单位（挂在军种或上级单位下）
            if parent_unit_id:
                parent_node = self._tree_model.get_node(parent_unit_id)
                if parent_node:
                    parent_id = parent_unit_id

            if parent_id:
                self._tree_model.add_unit(
                    unit_id=unit_id,
                    parent_id=parent_id,
                    unit_name=unit.get("unit_name", ""),
                    unit_level=unit.get("unit_level", ""),
                    unit_code=unit.get("unit_code"),
                    unit_type=unit.get("unit_type"),
                    commander=unit.get("commander"),
                    strength=unit.get("strength"),
                    location=location,
                )

            # 添加装备信息
            equipment_list = unit.get("equipment", [])
            for eq in equipment_list:
                self._tree_model.add_equipment(
                    unit_id=unit_id,
                    equipment_id=eq.get("equipment_id", ""),
                    equipment_name=eq.get("name", ""),
                    model_code=eq.get("model_code"),
                    equipment_type=eq.get("type"),
                    inventory_count=eq.get("inventory_count"),
                )

        # ── 网状图：基于指挥关系建立连接 ──
        self._build_network_from_units(units)
        self._data_loaded = True
        return self

    def _build_network_from_units(self, units: Dict) -> None:
        """从单位列表构建网状图"""
        # 建立 unit_id → 单位信息 的映射
        unit_map: Dict[str, Dict] = {u.get("unit_id", ""): u for u in units}
        added_nodes: set = set()

        for unit in units:
            unit_id = unit.get("unit_id", "")
            if unit_id in added_nodes:
                continue
            added_nodes.add(unit_id)

            country_name = unit.get("country_name", "未知国家")
            self._network_model.add_node(
                node_id=unit_id,
                name=unit.get("unit_name", ""),
                node_type="unit",
                data={
                    "unit_code": unit.get("unit_code"),
                    "unit_level": unit.get("unit_level"),
                    "country_name": country_name,
                    "branch_name": unit.get("branch_name"),
                    "commander": unit.get("commander"),
                    "strength": unit.get("strength"),
                    "location": unit.get("location"),
                },
            )

            # 添加指挥关系边（上级→下级）
            parent_id = unit.get("parent_unit_id")
            if parent_id and parent_id in unit_map:
                self._network_model.add_edge(
                    source_id=parent_id,
                    target_id=unit_id,
                    relation_type="command",
                    bidirectional=False,
                )

        # 额外添加国家和军种节点
        seen_countries: Dict[str, str] = {}
        seen_branches: Dict[str, str] = {}
        for unit in units:
            country_name = unit.get("country_name", "未知国家")
            branch_name = unit.get("branch_name", "未知军种")
            branch_key = f"{country_name}-{branch_name}"

            if country_name not in seen_countries:
                cid = f"country-{country_name}"
                self._network_model.add_node(
                    node_id=cid,
                    name=country_name,
                    node_type="country",
                    data={"country_name": country_name},
                )
                seen_countries[country_name] = cid

            if branch_key not in seen_branches:
                bid = f"branch-{branch_key}"
                self._network_model.add_node(
                    node_id=bid,
                    name=branch_name,
                    node_type="branch",
                    data={
                        "country_name": country_name,
                        "branch_name": branch_name,
                    },
                )
                seen_branches[branch_key] = bid

    def load_from_taiwan_json(self, json_path: str) -> "ViewModeSwitcher":
        """
        从 taiwan_units.json 加载示例数据
        
        Args:
            json_path: data/taiwan_units.json 的路径
        """
        import json
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 转换 JSON 格式 → 统一单位格式
        units = []
        country_name = data.get("country", {}).get("name_zh", "台湾地区")

        for unit in data.get("units", []):
            parent_code = unit.get("parent_unit_code")
            units.append(
                {
                    "unit_id": unit.get("unit_code"),
                    "unit_code": unit.get("unit_code"),
                    "unit_name": unit.get("unit_name"),
                    "unit_level": unit.get("unit_level"),
                    "unit_type": unit.get("unit_type"),
                    "country_name": country_name,
                    "branch_name": "陆军",  # taiwan_units.json 目前只有陆军数据
                    "parent_unit_id": parent_code,
                    "commander": unit.get("commander"),
                    "strength": unit.get("strength"),
                    "location": unit.get("location"),
                    "equipment": unit.get("equipment", []),
                }
            )

        return self.load_from_units(units)

    # ── 视图导出 ────────────────────────────────────────────────

    def get_current_view(self) -> Dict:
        """
        获取当前模式的视图数据
        
        Returns:
            dict: {
                "mode": "tree" | "network",
                "data": <TreeViewModel.get_tree_json() | GraphViewModel.get_graph_json()>,
            }
        """
        if self._mode == self.MODE_TREE:
            return {
                "mode": self.MODE_TREE,
                "data": self._tree_model.get_tree_json(),
            }
        else:
            return {
                "mode": self.MODE_NETWORK,
                "data": self._network_model.get_graph_json(),
            }

    def get_tree_view(self) -> Dict:
        """获取树状图数据"""
        return self._tree_model.get_tree_json()

    def get_network_view(self) -> Dict:
        """获取网状图数据（含力导向布局）"""
        self._network_model.force_directed_layout()
        return self._network_model.get_graph_json()

    def search(self, keyword: str) -> List[Dict]:
        """
        在当前模式下搜索节点
        
        Returns:
            list: 匹配的节点列表
        """
        if self._mode == self.MODE_TREE:
            return self._tree_model.search(keyword)
        else:
            return self._network_model.search_nodes(keyword)
