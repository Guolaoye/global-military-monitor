"""树状图视图"""
from typing import Dict, List

class TreeViewModel:
    """军事力量结构树状图模型"""
    
    def __init__(self):
        self.root = {"id": "root", "name": "全球军事", "children": []}
        self.node_map = {}
    
    def add_country(self, country_id: str, name: str):
        """添加国家节点"""
        node = {"id": country_id, "name": name, "children": []}
        self.node_map[country_id] = node
        self.root["children"].append(node)
    
    def add_branch(self, country_id: str, branch_id: str, name: str, branch_type: str):
        """添加军种节点"""
        if country_id in self.node_map:
            node = {"id": branch_id, "name": f"{name} ({branch_type})", "children": []}
            self.node_map[branch_id] = node
            self.node_map[country_id]["children"].append(node)
    
    def add_unit(self, parent_id: str, unit_id: str, name: str, unit_level: str):
        """添加单位节点"""
        if parent_id in self.node_map:
            node = {"id": unit_id, "name": f"{name} [{unit_level}]", "children": []}
            self.node_map[unit_id] = node
            self.node_map[parent_id]["children"].append(node)
    
    def get_tree(self) -> Dict:
        """获取完整的树结构"""
        return self.root
    
    def find_node(self, node_id: str) -> Dict:
        """查找节点"""
        return self.node_map.get(node_id, {})
