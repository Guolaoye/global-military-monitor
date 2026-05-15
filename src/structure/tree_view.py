"""军事力量结构 - 树状图视图（Xmind风格层级展示）

国家 → 军种 → 部队 → 营/连 层级展开/收起
"""
from typing import Dict, List, Optional, Any
import uuid


class TreeNode:
    """树节点"""
    
    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: str,  # country | branch | unit | subunit
        level: int,      # 0=全球根 1=国家 2=军种 3=部队 4=营/连
        data: Optional[Dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.level = level
        self.data = data or {}
        self.children: List["TreeNode"] = []
        self._expanded = level <= 2  # 默认展开到部队级别
    
    @property
    def is_expanded(self) -> bool:
        return self._expanded
    
    def expand(self):
        self._expanded = True
    
    def collapse(self):
        self._expanded = False
    
    def toggle(self):
        self._expanded = not self._expanded
    
    def add_child(self, child: "TreeNode"):
        self.children.append(child)
    
    def find_node(self, node_id: str) -> Optional["TreeNode"]:
        """递归查找节点"""
        if self.node_id == node_id:
            return self
        for child in self.children:
            found = child.find_node(node_id)
            if found:
                return found
        return None
    
    def to_dict(self, include_expanded: bool = True) -> Dict:
        result = {
            "id": self.node_id,
            "name": self.name,
            "type": self.node_type,
            "level": self.level,
            "data": self.data,
            "children": [c.to_dict(include_expanded) for c in self.children],
        }
        if include_expanded:
            result["expanded"] = self._expanded
        return result


class TreeViewModel:
    """
    军事力量结构树状图模型
    
    层级结构：全球 → 国家 → 军种 → 部队 → 营/连
    
    Usage:
        tree = TreeViewModel()
        tree.load_from_units(units_data)  # 从DB数据加载
        tree.expand("unit-001")            # 展开节点
        tree.collapse("unit-002")          # 收起节点
        json_data = tree.get_tree_json()   # 获取JSON供前端渲染
    """
    
    ROOT_ID = "global-military-root"
    
    def __init__(self):
        self.root = TreeNode(
            node_id=self.ROOT_ID,
            name="全球军事力量",
            node_type="root",
            level=0,
            data={},
        )
        self._node_map: Dict[str, TreeNode] = {self.ROOT_ID: self.root}
    
    def add_country(
        self,
        country_id: str,
        name_zh: str,
        name_en: Optional[str] = None,
        region: Optional[str] = None,
    ) -> TreeNode:
        """添加国家节点"""
        node = TreeNode(
            node_id=country_id,
            name=name_zh,
            node_type="country",
            level=1,
            data={"name_en": name_en, "region": region},
        )
        self.root.add_child(node)
        self._node_map[country_id] = node
        return node
    
    def add_branch(
        self,
        branch_id: str,
        country_id: str,
        name_zh: str,
        name_en: Optional[str] = None,
        branch_type: Optional[str] = None,  # army | navy | air_force | rocket | reserve
    ) -> Optional[TreeNode]:
        """添加军种节点（陆/海/空/火箭军/后备等）"""
        parent = self._node_map.get(country_id)
        if not parent:
            return None
        
        node = TreeNode(
            node_id=branch_id,
            name=name_zh,
            node_type="branch",
            level=2,
            data={
                "name_en": name_en,
                "branch_type": branch_type,
                "country_id": country_id,
            },
        )
        parent.add_child(node)
        self._node_map[branch_id] = node
        return node
    
    def add_unit(
        self,
        unit_id: str,
        parent_id: str,
        unit_name: str,
        unit_level: str,  # 战区 | 军团 | 旅 | 营 | 连
        unit_code: Optional[str] = None,
        unit_type: Optional[str] = None,
        commander: Optional[str] = None,
        strength: Optional[int] = None,
        location: Optional[Dict] = None,
    ) -> Optional[TreeNode]:
        """添加单位节点"""
        parent = self._node_map.get(parent_id)
        if not parent:
            return None
        
        # 根据父节点层级推断当前层级
        level = parent.level + 1
        
        node = TreeNode(
            node_id=unit_id,
            name=unit_name,
            node_type="unit",
            level=level,
            data={
                "unit_code": unit_code,
                "unit_level": unit_level,
                "unit_type": unit_type,
                "commander": commander,
                "strength": strength,
                "location": location,
                "parent_id": parent_id,
            },
        )
        parent.add_child(node)
        self._node_map[unit_id] = node
        return node
    
    def add_equipment(
        self,
        unit_id: str,
        equipment_id: str,
        equipment_name: str,
        model_code: Optional[str] = None,
        equipment_type: Optional[str] = None,
        inventory_count: Optional[int] = None,
        specifications: Optional[Dict] = None,
    ) -> bool:
        """为单位节点附加装备信息"""
        node = self._node_map.get(unit_id)
        if not node:
            return False
        
        if "equipment" not in node.data:
            node.data["equipment"] = []
        
        node.data["equipment"].append({
            "equipment_id": equipment_id,
            "name": equipment_name,
            "model_code": model_code,
            "type": equipment_type,
            "inventory_count": inventory_count,
            "specifications": specifications or {},
        })
        return True
    
    def get_node(self, node_id: str) -> Optional[TreeNode]:
        return self._node_map.get(node_id)
    
    def expand(self, node_id: str) -> bool:
        node = self._node_map.get(node_id)
        if node:
            node.expand()
            return True
        return False
    
    def collapse(self, node_id: str) -> bool:
        node = self._node_map.get(node_id)
        if node:
            node.collapse()
            return True
        return False
    
    def toggle(self, node_id: str) -> bool:
        node = self._node_map.get(node_id)
        if node:
            node.toggle()
            return True
        return False
    
    def get_ancestors(self, node_id: str) -> List[str]:
        """获取节点的祖先路径"""
        ancestors = []
        node = self._node_map.get(node_id)
        while node and node.level > 0:
            if node.node_type != "root":
                ancestors.append(node.node_id)
            # 向上查找父节点
            parent_id = node.data.get("parent_id")
            if node.node_type == "unit":
                parent_id = node.data.get("parent_id")
            else:
                parent_id = None
            node = self._node_map.get(parent_id) if parent_id else None
        return ancestors
    
    def get_subtree(self, node_id: str, max_depth: int = -1) -> Optional[Dict]:
        """获取子树（用于按需加载子节点）"""
        node = self._node_map.get(node_id)
        if not node:
            return None
        return node.to_dict()
    
    def get_tree_json(self) -> Dict:
        """获取完整树结构（供前端渲染）"""
        return self.root.to_dict()
    
    def load_from_dict(self, data: Dict) -> bool:
        """从字典数据加载整棵树"""
        try:
            self._load_node_recursive(self.root, data.get("children", []))
            return True
        except Exception as e:
            print(f"加载树数据失败: {e}")
            return False
    
    def _load_node_recursive(self, parent: TreeNode, children_data: List[Dict]):
        for child_data in children_data:
            node = TreeNode(
                node_id=child_data["id"],
                name=child_data["name"],
                node_type=child_data["type"],
                level=child_data["level"],
                data=child_data.get("data", {}),
            )
            if child_data.get("expanded") is not None:
                if child_data["expanded"]:
                    node.expand()
                else:
                    node.collapse()
            parent.add_child(node)
            self._node_map[node.node_id] = node
            if child_data.get("children"):
                self._load_node_recursive(node, child_data["children"])
    
    def get_breadcrumb(self, node_id: str) -> List[str]:
        """获取节点的面包屑路径"""
        ancestors = self.get_ancestors(node_id)
        path = []
        for aid in reversed(ancestors):
            node = self._node_map.get(aid)
            if node:
                path.append(f"{node.name}")
        return path
    
    def search(self, keyword: str) -> List[Dict]:
        """搜索节点"""
        results = []
        self._search_recursive(self.root, keyword, results)
        return results
    
    def _search_recursive(self, node: TreeNode, keyword: str, results: List[Dict]):
        if keyword.lower() in node.name.lower():
            results.append({
                "node_id": node.node_id,
                "name": node.name,
                "type": node.node_type,
                "breadcrumb": self.get_breadcrumb(node.node_id),
            })
        for child in node.children:
            self._search_recursive(child, keyword, results)
    
    def get_stats(self) -> Dict:
        """获取树统计信息"""
        stats = {"countries": 0, "branches": 0, "units": 0}
        self._count_recursive(self.root, stats)
        return stats
    
    def _count_recursive(self, node: TreeNode, stats: Dict):
        if node.node_type == "country":
            stats["countries"] += 1
        elif node.node_type == "branch":
            stats["branches"] += 1
        elif node.node_type == "unit":
            stats["units"] += 1
        for child in node.children:
            self._count_recursive(child, stats)