# -*- coding: utf-8 -*-
"""
AI辅助分析模块
集成AI引擎进行态势分析和决策建议
支持MiniMax API和其他AI服务
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.config import load_config


class AIAssistant:
    """
    AI辅助分析器
    
    提供军事态势智能分析能力：
    - 地形分析
    - 气象影响评估
    - 威胁评估
    - 行动建议生成
    """
    
    def __init__(self):
        self.config = load_config()
        self.api_key = self.config.get('AI_API_KEY', '')
        self.api_base = self.config.get('AI_API_BASE', 'https://api.minimax.chat/v1')
        self.model = self.config.get('AI_MODEL', 'abab6-chat')
        self.use_mock = not self.api_key or self.api_key == 'your-api-key'
        
        if self.use_mock:
            print("[AI助手] 使用模拟模式（未配置API密钥）")
        else:
            print(f"[AI助手] 使用真实API: {self.model}")
    
    def analyze_situation(
        self, 
        positions: List[Dict[str, Any]], 
        event_type: str = 'situational_analysis'
    ) -> Dict[str, Any]:
        """
        分析军事态势
        
        Args:
            positions: 位置数据列表
            event_type: 事件类型标识
            
        Returns:
            分析结果字典
        """
        try:
            # 构建分析上下文
            context = self._build_analysis_context(positions, event_type)
            
            if self.use_mock:
                # 使用模拟分析
                return self._mock_analysis(context)
            else:
                # 调用真实API
                return self._call_ai_api(context)
                
        except Exception as e:
            print(f"态势分析失败: {e}")
            return self._generate_error_result(str(e))
    
    def _build_analysis_context(
        self, 
        positions: List[Dict[str, Any]], 
        event_type: str
    ) -> Dict[str, Any]:
        """构建分析上下文"""
        # 统计位置数据
        unit_stats = self._calculate_position_statistics(positions)
        
        # 识别国家分布
        country_distribution = self._analyze_country_distribution(positions)
        
        # 检测聚集区域
        clusters = self._detect_clusters(positions)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'positions': positions,
            'unit_statistics': unit_stats,
            'country_distribution': country_distribution,
            'clusters': clusters,
            'total_positions': len(positions)
        }
    
    def _calculate_position_statistics(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算位置统计信息"""
        if not positions:
            return {'count': 0, 'units': []}
        
        # 按单位分组
        units = {}
        for pos in positions:
            unit_id = pos.get('unit_id', 'unknown')
            if unit_id not in units:
                units[unit_id] = {
                    'name': pos.get('unit_name', '未知单位'),
                    'type': pos.get('unit_type', '未知类型'),
                    'position_count': 0,
                    'latest_lat': pos.get('latitude', 0),
                    'latest_lng': pos.get('longitude', 0)
                }
            units[unit_id]['position_count'] += 1
        
        # 计算覆盖区域
        lats = [p.get('latitude', 0) for p in positions if p.get('latitude')]
        lons = [p.get('longitude', 0) for p in positions if p.get('longitude')]
        
        coverage = {}
        if lats and lons:
            coverage = {
                'min_lat': min(lats),
                'max_lat': max(lats),
                'min_lng': min(lons),
                'max_lng': max(lons),
                'center_lat': sum(lats) / len(lats),
                'center_lng': sum(lons) / len(lons)
            }
        
        return {
            'count': len(positions),
            'unique_units': len(units),
            'units': list(units.values()),
            'coverage': coverage
        }
    
    def _analyze_country_distribution(self, positions: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析国家分布"""
        distribution = {}
        for pos in positions:
            country = pos.get('country_name', '未知')
            distribution[country] = distribution.get(country, 0) + 1
        return distribution
    
    def _detect_clusters(self, positions: List[Dict[str, Any]], threshold_km: float = 100) -> List[Dict[str, Any]]:
        """检测单位聚集区域"""
        if len(positions) < 3:
            return []
        
        clusters = []
        
        # 简化的聚类算法：按网格划分
        grid_size = 2.0  # 度（约200km）
        
        grid = {}
        for pos in positions:
            lat = pos.get('latitude', 0)
            lng = pos.get('longitude', 0)
            grid_key = f"{int(lat/grid_size)},{int(lng/grid_size)}"
            
            if grid_key not in grid:
                grid[grid_key] = {
                    'count': 0,
                    'lat_sum': 0,
                    'lng_sum': 0,
                    'positions': []
                }
            
            grid[grid_key]['count'] += 1
            grid[grid_key]['lat_sum'] += lat
            grid[grid_key]['lng_sum'] += lng
            grid[grid_key]['positions'].append(pos)
        
        # 筛选密集区域
        for key, data in grid.items():
            if data['count'] >= 3:  # 至少3个单位
                clusters.append({
                    'center_lat': data['lat_sum'] / data['count'],
                    'center_lng': data['lng_sum'] / data['count'],
                    'unit_count': data['count'],
                    'description': f"检测到{data['count']}个单位聚集"
                })
        
        return clusters
    
    def _call_ai_api(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用AI API进行分析
        
        Args:
            context: 分析上下文
            
        Returns:
            AI分析结果
        """
        try:
            import requests
            
            # 构建提示词
            prompt = self._build_analysis_prompt(context)
            
            # API调用
            url = f"{self.api_base}/text/chatcompletion_v2"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是一位专业的军事态势分析专家，擅长分析军事部署、评估威胁等级、提供决策建议。请用中文回答。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1500
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                return self._parse_ai_response(content, context)
            else:
                print(f"API调用失败: {response.status_code}")
                return self._mock_analysis(context)
                
        except Exception as e:
            print(f"API调用异常: {e}")
            return self._mock_analysis(context)
    
    def _build_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """构建分析提示词"""
        stats = context.get('unit_statistics', {})
        coverage = stats.get('coverage', {})
        clusters = context.get('clusters', [])
        
        prompt = f"""
请分析以下军事态势数据：

【态势概况】
- 位置记录总数：{context['total_positions']}
- 涉及单位数：{stats.get('unique_units', 0)}
- 覆盖区域中心：纬度 {coverage.get('center_lat', 'N/A'):.4f}，经度 {coverage.get('center_lng', 'N/A'):.4f}

【国家分布】
{json.dumps(context.get('country_distribution', {}), ensure_ascii=False, indent=2)}

【聚集区域】
"""
        
        if clusters:
            for i, cluster in enumerate(clusters[:3], 1):
                prompt += f"\n{i}. 中心点({cluster['center_lat']:.4f}, {cluster['center_lng']:.4f})，单位数：{cluster['unit_count']}"
        else:
            prompt += "\n未检测到明显聚集区域"
        
        prompt += """

请提供以下分析：
1. 地形分析：评估该区域的战术地形特征
2. 气象影响：评估当前气象条件对军事行动的影响
3. 威胁评估：分析潜在威胁来源和威胁等级
4. 行动建议：给出具体的作战或监控建议

请用结构化的中文回复。
"""
        
        return prompt
    
    def _parse_ai_response(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI响应"""
        # 简单解析响应内容
        result = {
            'timestamp': context['timestamp'],
            'analysis_type': 'ai_generated',
            'raw_content': content,
            'terrain_analysis': '',
            'weather_impact': '',
            'threat_assessment': '',
            'recommendation': ''
        }
        
        # 尝试分段提取
        sections = content.split('\n\n')
        for section in sections:
            section = section.strip()
            if '地形' in section:
                result['terrain_analysis'] = section
            elif '气象' in section or '天气' in section:
                result['weather_impact'] = section
            elif '威胁' in section:
                result['threat_assessment'] = section
            elif '建议' in section or '行动' in section:
                result['recommendation'] = section
        
        # 如果解析不完整，使用完整内容
        if not result['recommendation']:
            result['recommendation'] = content
        
        return result
    
    def _mock_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成模拟分析结果（当无API密钥时使用）
        
        Args:
            context: 分析上下文
            
        Returns:
            模拟分析结果
        """
        stats = context.get('unit_statistics', {})
        coverage = stats.get('coverage', {})
        clusters = context.get('clusters', [])
        countries = context.get('country_distribution', {})
        
        # 生成模拟分析
        terrain_analysis = self._generate_mock_terrain_analysis(coverage)
        weather_impact = self._generate_mock_weather_impact(context)
        threat_assessment = self._generate_mock_threat_assessment(context, countries)
        recommendation = self._generate_mock_recommendation(context, clusters)
        
        return {
            'timestamp': context['timestamp'],
            'analysis_type': 'mock',
            'terrain_analysis': terrain_analysis,
            'weather_impact': weather_impact,
            'threat_assessment': threat_assessment,
            'recommendation': recommendation
        }
    
    def _generate_mock_terrain_analysis(self, coverage: Dict[str, float]) -> str:
        """生成模拟地形分析"""
        center_lat = coverage.get('center_lat', 0)
        center_lng = coverage.get('center_lng', 0)
        
        # 基于坐标模拟地形特征
        if center_lat > 45:
            terrain_type = "高纬度区域，地形多为丘陵和高原"
            terrain_score = 65
        elif center_lat > 35:
            terrain_type = "中纬度区域，地形多样，包括平原和山地"
            terrain_score = 55
        else:
            terrain_type = "低纬度区域，地形多为平原和丘陵"
            terrain_score = 45
        
        return f"""【地形分析】
区域中心坐标: ({center_lat:.4f}, {center_lng:.4f})

地形特征: {terrain_type}

地形评分: {terrain_score}/100
- 防御优势: {'中等' if 40 < terrain_score < 70 else '明显' if terrain_score >= 70 else '较弱'}
- 机动性: {'良好' if terrain_score < 50 else '一般' if terrain_score < 70 else '受限'}
- 隐蔽条件: {'良好' if terrain_score > 60 else '一般'}

战术评估：该区域{'适合建立防御阵地' if terrain_score > 60 else '适合快速机动部署' if terrain_score < 50 else '需要根据具体任务灵活应对'}"""
    
    def _generate_mock_weather_impact(self, context: Dict[str, Any]) -> str:
        """生成模拟气象影响分析"""
        import random
        
        weather_conditions = ['晴朗', '多云', '阴天', '小雨', '大雾']
        visibility_range = ['10km以上', '5-10km', '2-5km', '1-2km']
        
        weather = random.choice(weather_conditions)
        visibility = random.choice(visibility_range)
        wind_speed = random.randint(0, 20)
        
        # 评估影响
        if '雾' in weather:
            air_impact = '严重受限'
            ground_impact = '轻度受限'
        elif '雨' in weather:
            air_impact = '明显受限'
            ground_impact = '受限'
        else:
            air_impact = '适宜'
            ground_impact = '适宜'
        
        return f"""【气象影响评估】
当前天气: {weather}
能见度: {visibility}
风速: {wind_speed}m/s

行动影响评估:
- 空中行动: {air_impact}
- 地面行动: {ground_impact}

综合评价: 当前气象条件{'对军事行动有利' if air_impact == '适宜' and ground_impact == '适宜' else '需注意天气变化'}

建议: {'保持正常监控' if air_impact == '适宜' else '建议启用备用方案或调整行动时间'}"""
    
    def _generate_mock_threat_assessment(
        self, 
        context: Dict[str, Any],
        countries: Dict[str, int]
    ) -> str:
        """生成模拟威胁评估"""
        total_units = context.get('unit_statistics', {}).get('unique_units', 0)
        clusters = context.get('clusters', [])
        
        # 基于国家分布评估威胁
        threat_countries = []
        for country, count in sorted(countries.items(), key=lambda x: -x[1]):
            if count >= 2:
                threat_countries.append(f"{country}({count}个单位)")
        
        # 基于聚集区域评估
        cluster_risk = '无' if not clusters else f"{len(clusters)}个密集区域"
        
        # 计算威胁等级
        threat_level = '低'
        if total_units >= 20 or len(clusters) >= 3:
            threat_level = '极高'
        elif total_units >= 10 or len(clusters) >= 2:
            threat_level = '高'
        elif total_units >= 5:
            threat_level = '中'
        
        return f"""【威胁评估】
威胁等级: {threat_level}

主要威胁来源:
{chr(10).join([f'- {c}' for c in threat_countries]) if threat_countries else '- 暂无明确威胁'}

聚集区域: {cluster_risk}

威胁特征:
- 单位密度: {'高密度' if clusters else '分散部署'}
- 协同可能性: {'存在联合行动风险' if clusters else '独立行动'}

结论: {'建议提高警戒级别' if threat_level in ['高', '极高'] else '维持常规监控'}"""
    
    def _generate_mock_recommendation(
        self, 
        context: Dict[str, Any],
        clusters: List[Dict[str, Any]]
    ) -> str:
        """生成模拟行动建议"""
        total_positions = context['total_positions']
        unique_units = context.get('unit_statistics', {}).get('unique_units', 0)
        
        recommendations = []
        
        # 基础建议
        recommendations.append("1. 加强区域监控，增加侦察频次")
        
        # 基于单位数量
        if unique_units > 10:
            recommendations.append("2. 建议部署更多传感器覆盖该区域")
            recommendations.append("3. 通知相关部门保持警戒")
        elif unique_units > 5:
            recommendations.append("2. 维持正常监控频率")
        
        # 基于聚集区域
        if clusters:
            for i, cluster in enumerate(clusters[:2], 1):
                lat = cluster.get('center_lat', 0)
                lng = cluster.get('center_lng', 0)
                count = cluster.get('unit_count', 0)
                recommendations.append(f"{len(recommendations)+1}. 重点关注聚集区域{i}: ({lat:.2f}, {lng:.2f})，{count}个单位")
        
        # 行动建议
        recommendations.append(f"{len(recommendations)+1}. {'建议实时追踪' if unique_units > 10 else '建议定时巡查'}")
        
        action_type = '高强度监控'
        if total_positions < 50:
            action_type = '常规监控'
        elif total_positions < 100:
            action_type = '加强监控'
        
        summary = f"""【行动建议】

总体方案: {action_type}

具体建议:
{chr(10).join(recommendations)}

优先级: {'高' if unique_units > 10 else '中' if unique_units > 5 else '低'}

执行时间: 立即生效，持续监控至态势稳定"""
        
        return summary
    
    def _generate_error_result(self, error_message: str) -> Dict[str, Any]:
        """生成错误结果"""
        return {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'error',
            'error': error_message,
            'terrain_analysis': f'分析失败: {error_message}',
            'weather_impact': '无法获取',
            'threat_assessment': '无法评估',
            'recommendation': '请稍后重试'
        }
    
    def quick_analyze(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        快速单点分析
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            简化分析结果
        """
        from src.situational_real.terrain_analysis import TerrainAnalysis
        
        terrain = TerrainAnalysis()
        result = terrain.combined_analysis(lat, lng, units=[])
        
        return {
            'coordinate': {'lat': lat, 'lng': lng},
            'terrain_score': result.get('terrain_analysis', {}).get('score', 0),
            'terrain_type': result.get('terrain_analysis', {}).get('type', 'unknown'),
            'weather': result.get('weather_impact', '未知'),
            'threat_level': result.get('threat_level', '未知'),
            'recommendation': result.get('recommendation', '暂无')
        }


if __name__ == '__main__':
    # 测试代码
    assistant = AIAssistant()
    
    # 模拟位置数据
    test_positions = [
        {'unit_id': 1, 'unit_name': '单位A', 'unit_type': 'aircraft', 'latitude': 39.9, 'longitude': 116.4, 'country_name': '中国'},
        {'unit_id': 2, 'unit_name': '单位B', 'unit_type': 'artillery', 'latitude': 40.0, 'longitude': 116.5, 'country_name': '中国'},
        {'unit_id': 3, 'unit_name': '单位C', 'unit_type': 'aircraft', 'latitude': 39.8, 'longitude': 116.3, 'country_name': '美国'},
    ]
    
    print("=" * 60)
    print("AI辅助态势分析测试")
    print("=" * 60)
    
    result = assistant.analyze_situation(test_positions, 'test_analysis')
    
    print(f"\n分析时间: {result['timestamp']}")
    print(f"分析类型: {result['analysis_type']}")
    print(f"\n【地形分析】\n{result['terrain_analysis']}")
    print(f"\n【气象影响】\n{result['weather_impact']}")
    print(f"\n【威胁评估】\n{result['threat_assessment']}")
    print(f"\n【行动建议】\n{result['recommendation']}")
    
    # 快速分析测试
    print("\n" + "=" * 60)
    print("快速单点分析测试")
    print("=" * 60)
    
    quick = assistant.quick_analyze(39.9042, 116.4074)
    print(f"坐标: ({quick['coordinate']['lat']}, {quick['coordinate']['lng']})")
    print(f"地形评分: {quick['terrain_score']}")
    print(f"威胁等级: {quick['threat_level']}")
    print(f"建议: {quick['recommendation']}")
