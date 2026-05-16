"""网状图视图"""
from typing import Dict, List, Set

class GraphViewModel:
    """军事力量结构网状图模型"""
    
    def __init__(self):
        self.nodes = {}  # node_id -> {id, name, type, x, y}
        self.edges = []  # [(source_id, target_id), ...]
        self.adjacency = {}  # node_id -> [connected_node_ids]
    
    def add_node(self, node_id: str, name: str, node_type: str):
        """添加节点"""
        self.nodes[node_id] = {"id": node_id, "name": name, "type": node_type}
        self.adjacency[node_id] = []
    
    def add_edge(self, source_id: str, target_id: str):
        """添加边"""
        if source_id in self.nodes and target_id in self.nodes:
            self.edges.append((source_id, target_id))
            self.adjacency[source_id].append(target_id)
            self.adjacency[target_id].append(source_id)
    
    def get_nodes(self) -> List[Dict]:
        """获取所有节点"""
        return list(self.nodes.values())
    
    def get_edges(self) -> List:
        """获取所有边"""
        return self.edges
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """获取邻居节点"""
        return self.adjacency.get(node_id, [])
    
    def clear(self):
        """清空图"""
        self.nodes.clear()
        self.edges.clear()
        self.adjacency.clear()
