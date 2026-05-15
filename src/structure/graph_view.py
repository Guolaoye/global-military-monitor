"""军事力量结构 - 网状图视图（Obsidian双向链接风格）

单位之间可建立关系线，支持展示：
- 指挥关系（上级/下级）
- 协同关系（友邻单位）
- 对抗关系（假想敌）
- 支援关系（后勤/火力支援）
"""
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import defaultdict
import math


class GraphNode:
    """网状图节点"""
    
    TYPE_UNIT = "unit"
    TYPE_BRANCH = "branch"
    TYPE_EQUIPMENT = "equipment"
    TYPE_COUNTRY = "country"
    
    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: str = TYPE_UNIT,
        x: float = 0.0,
        y: float = 0.0,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.x = x
        self.y = y
        self.data = data or {}
        self._connections: Set[str] = set()
    
    def add_connection(self, neighbor_id: str):
        self._connections.add(neighbor_id)
    
    def remove_connection(self, neighbor_id: str):
        self._connections.discard(neighbor_id)
    
    def get_connections(self) -> Set[str]:
        return self._connections.copy()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.node_id,
            "name": self.name,
            "type": self.node_type,
            "x": self.x,
            "y": self.y,
            "data": self.data,
            "connections": list(self._connections),
        }


class GraphEdge:
    """网状图边（关系线）"""
    
    REL_COMMAND = "command"       # 指挥关系
    REL_COORDINATION = "coordination"  # 协同关系
    REL_ADVERSARY = "adversary"   # 对抗关系
    REL_SUPPORT = "support"       # 支援关系
    REL_LOGISTICS = "logistics"   # 后勤关系
    REL_SAME_AS = "same_as"       # 同级关系
    
    def __init__(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = REL_COMMAND,
        weight: float = 1.0,
        label: Optional[str] = None,
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.weight = weight
        self.label = label
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type,
            "weight": self.weight,
            "label": self.label,
        }


class GraphViewModel:
    """
    军事力量结构网状图模型
    
    支持多种关系类型，与 Obsidian 双向链接图谱类似：
    - 指挥链（command）：上下级关系，实线
    - 协同（coordination）：友邻单位，虚线
    - 对抗（adversary）：假想敌，红色
    - 支援（support）：支援关系，蓝色虚线
    
    Usage:
        graph = GraphViewModel()
        graph.load_from_tree(tree_model)  # 从树状图模型加载
        graph.add_edge("unit-001", "unit-002", "coordination")
        json_data = graph.get_graph_json()  # 供前端渲染
    """
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._country_colors = [
            "#4A90D9", "#50C878", "#E53935", "#FF9800",
            "#9C27B0", "#00BCD4", "#795548", "#607D8B",
        ]
    
    def add_node(
        self,
        node_id: str,
        name: str,
        node_type: str = GraphNode.TYPE_UNIT,
        x: float = 0.0,
        y: float = 0.0,
        data: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        """添加节点"""
        node = GraphNode(node_id, name, node_type, x, y, data)
        self.nodes[node_id] = node
        self._adjacency[node_id] = set()
        return node
    
    def update_node_position(self, node_id: str, x: float, y: float) -> bool:
        """更新节点位置（用于力导向布局后的坐标保存）"""
        node = self.nodes.get(node_id)
        if node:
            node.x = x
            node.y = y
            return True
        return False
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = GraphEdge.REL_COMMAND,
        weight: float = 1.0,
        label: Optional[str] = None,
        bidirectional: bool = True,
    ) -> bool:
        """添加边（单位关系）"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
        
        edge = GraphEdge(source_id, target_id, relation_type, weight, label)
        self.edges.append(edge)
        
        self.nodes[source_id].add_connection(target_id)
        self._adjacency[source_id].add(target_id)
        if bidirectional:
            self.nodes[target_id].add_connection(source_id)
            self._adjacency[target_id].add(source_id)
        return True
    
    def remove_edge(self, source_id: str, target_id: str, relation_type: Optional[str] = None) -> bool:
        """移除边"""
        for i, edge in enumerate(self.edges):
            if edge.source_id == source_id and edge.target_id == target_id:
                if relation_type is None or edge.relation_type == relation_type:
                    self.edges.pop(i)
                    self.nodes[source_id].remove_connection(target_id)
                    self._adjacency[source_id].discard(target_id)
                    return True
        return False
    
    def get_neighbors(self, node_id: str, relation_type: Optional[str] = None) -> List[str]:
        """获取邻居节点"""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id:
                if relation_type is None or edge.relation_type == relation_type:
                    neighbors.append(edge.target_id)
            if edge.target_id == node_id:
                if relation_type is None or edge.relation_type == relation_type:
                    neighbors.append(edge.source_id)
        return neighbors
    
    def get_edges_for_node(self, node_id: str) -> List[Dict]:
        """获取节点的所有边"""
        result = []
        for edge in self.edges:
            if edge.source_id == node_id or edge.target_id == node_id:
                result.append(edge.to_dict())
        return result
    
    def load_from_tree(self, tree_model, country_color_map: Optional[Dict[str, str]] = None) -> int:
        """
        从 TreeViewModel 加载数据，生成网状图
        
        Args:
            tree_model: TreeViewModel 实例
            country_color_map: 国家ID -> 颜色 映射
        
        Returns:
            int: 加载的节点数
        """
        if country_color_map is None:
            country_color_map = {}
        
        tree_data = tree_model.get_tree_json()
        loaded = 0
        country_idx = {}
        color_idx = 0
        
        def process_node(node_dict: Dict, parent_data: Optional[Dict] = None):
            nonlocal color_idx, loaded
            
            node_id = node_dict["id"]
            name = node_dict["name"]
            node_type = node_dict["type"]
            data = node_dict.get("data", {})
            
            if node_type in ("country", "branch", "unit"):
                # 计算颜色
                if node_type == "country":
                    color = country_color_map.get(node_id)
                    if not color:
                        color = self._country_colors[color_idx % len(self._country_colors)]
                        country_color_map[node_id] = color
                        color_idx += 1
                    country_idx[node_id] = color
                
                node_color = country_idx.get(data.get("country_id", ""), "#808080")
                
                self.add_node(
                    node_id=node_id,
                    name=name,
                    node_type=node_type,
                    data={
                        **data,
                        "color": node_color,
                    },
                )
                loaded += 1
                
                # 添加到父节点的指挥关系边
                if parent_data:
                    self.add_edge(
                        source_id=parent_data["id"],
                        target_id=node_id,
                        relation_type=GraphEdge.REL_COMMAND,
                        bidirectional=False,
                    )
                
                # 递归处理子节点
                for child in node_dict.get("children", []):
                    process_node(child, {"id": node_id, "type": node_type})
        
        # 处理树根的子节点（国家级别）
        for child in tree_data.get("children", []):
            process_node(child, None)
        
        return loaded
    
    def force_directed_layout(
        self,
        iterations: int = 100,
        repulsion_strength: float = 5000.0,
        attraction_strength: float = 0.1,
        damping: float = 0.9,
    ) -> None:
        """
        力导向布局算法（ Fruchterman-Reingold）
        
        使节点在二维空间均匀分布，相关的节点靠近，无关的节点远离。
        """
        if not self.nodes:
            return
        
        # 初始化随机位置
        import random
        random.seed(42)
        for node in self.nodes.values():
            node.x = random.uniform(-500, 500)
            node.y = random.uniform(-500, 500)
        
        nodes_list = list(self.nodes.values())
        n = len(nodes_list)
        
        for iteration in range(iterations):
            # 计算温度（随迭代递减）
            temp = 500 * (1 - iteration / iterations)
            
            # 初始化位移
            displacements = {n.node_id: (0.0, 0.0) for n in nodes_list}
            
            # 互斥力（所有节点之间）
            for i in range(n):
                for j in range(i + 1, n):
                    ni = nodes_list[i]
                    nj = nodes_list[j]
                    
                    dx = ni.x - nj.x
                    dy = ni.y - nj.y
                    dist = math.sqrt(dx * dx + dy * dy) + 0.01
                    
                    repulsion = repulsion_strength * temp / (dist * dist)
                    fx = repulsion * dx / dist
                    fy = repulsion * dy / dist
                    
                    disp_i = displacements[ni.node_id]
                    disp_j = displacements[nj.node_id]
                    displacements[ni.node_id] = (disp_i[0] + fx, disp_i[1] + fy)
                    displacements[nj.node_id] = (disp_j[0] - fx, disp_j[1] - fy)
            
            # 吸引力（相邻节点之间）
            for edge in self.edges:
                ni = self.nodes.get(edge.source_id)
                nj = self.nodes.get(edge.target_id)
                if not ni or not nj:
                    continue
                
                dx = ni.x - nj.x
                dy = ni.y - nj.y
                dist = math.sqrt(dx * dx + dy * dy) + 0.01
                
                attraction = attraction_strength * dist * edge.weight
                fx = attraction * dx / dist
                fy = attraction * dy / dist
                
                disp_i = displacements[ni.node_id]
                disp_j = displacements[nj.node_id]
                displacements[ni.node_id] = (disp_i[0] - fx, disp_i[1] - fy)
                displacements[nj.node_id] = (disp_j[0] + fx, disp_j[1] + fy)
            
            # 应用位移
            for node in nodes_list:
                disp = displacements[node.node_id]
                dx, dy = disp
                dist = math.sqrt(dx * dx + dy * dy)
                
                if dist > temp:
                    dx = dx * temp / dist
                    dy = dy * temp / dist
                
                node.x += dx * damping
                node.y += dy * damping
                
                # 边界约束
                node.x = max(-800, min(800, node.x))
                node.y = max(-800, min(800, node.y))
    
    def get_graph_json(self) -> Dict:
        """获取网状图完整数据（供前端渲染）"""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "node_types": self._count_by_type(),
                "edge_types": self._count_edges_by_type(),
            },
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for node in self.nodes.values():
            counts[node.node_type] += 1
        return dict(counts)
    
    def _count_edges_by_type(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for edge in self.edges:
            counts[edge.relation_type] += 1
        return dict(counts)
    
    def find_shortest_path(self, source_id: str, target_id: str) -> List[str]:
        """BFS 查找最短路径（两单位之间的指挥链）"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        
        visited = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == target_id:
                return path
            
            for neighbor in self.get_neighbors(current, GraphEdge.REL_COMMAND):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def clear(self):
        """清空图数据"""
        self.nodes.clear()
        self.edges.clear()
        self._adjacency.clear()
    
    def search_nodes(self, keyword: str) -> List[Dict]:
        """搜索节点"""
        results = []
        for node in self.nodes.values():
            if keyword.lower() in node.name.lower():
                results.append({
                    "id": node.node_id,
                    "name": node.name,
                    "type": node.node_type,
                    "connection_count": len(node.get_connections()),
                })
        return results