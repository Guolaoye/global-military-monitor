"""态势推演辅助AI"""
import sys
import os
from typing import List, Dict, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)


class SituationAdvisor:
    """态势推演辅助分析器"""

    def __init__(self):
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            from src.config import load_config
            self.config = load_config()
        except Exception:
            self.config = {}

    def advise_real(self, positions: List[dict], history: List[dict] = None) -> dict:
        """
        真实态势推演辅助

        Args:
            positions: 当前单位位置列表
            history: 历史轨迹数据

        Returns:
            dict: {
                "next_moves": List[str],
                "risk_zones": List[dict],
                "force_analysis": dict,
                "recommendations": List[str],
            }
        """
        result = {
            "next_moves": [],
            "risk_zones": [],
            "force_analysis": {},
            "recommendations": [],
        }

        if not positions:
            return result

        # 1. 分析力量对比
        force_analysis = self._analyze_force_balance(positions)
        result["force_analysis"] = force_analysis

        # 2. 预测下一步行动
        result["next_moves"] = self._predict_next_moves(positions, history)

        # 3. 识别风险区域
        result["risk_zones"] = self._identify_risk_zones(positions)

        # 4. 生成建议
        result["recommendations"] = self._generate_recommendations(result)

        return result

    def advise_sim(self, sim_units: List[dict], weather: dict = None) -> dict:
        """
        模拟态势推演辅助

        Args:
            sim_units: 模拟单位列表
            weather: 天气数据

        Returns:
            dict: {
                "damage_coefficients": dict,
                "weather_impact": dict,
                "force_comparison": dict,
                "simulation_tips": List[str],
            }
        """
        result = {
            "damage_coefficients": {},
            "weather_impact": {},
            "force_comparison": {},
            "simulation_tips": [],
        }

        # 1. 计算毁伤系数
        result["damage_coefficients"] = self._calculate_damage_coefficients(sim_units)

        # 2. 天气影响
        if weather:
            result["weather_impact"] = self._analyze_weather_impact(sim_units, weather)

        # 3. 力量对比
        result["force_comparison"] = self._compare_forces(sim_units)

        # 4. 模拟建议
        result["simulation_tips"] = self._generate_sim_tips(result)

        return result

    def detect_anomaly(self, positions: List[dict]) -> List[dict]:
        """
        检测态势数据异常

        Args:
            positions: 当前单位位置列表

        Returns:
            List[dict]: 异常告警列表
        """
        anomalies = []

        if not positions:
            return anomalies

        # 检测1：单位突然移动
        anomalies.extend(self._check_sudden_movement(positions))

        # 检测2：异常集结
        anomalies.extend(self._check_unusual_concentration(positions))

        # 检测3：力量失衡
        anomalies.extend(self._check_force_imbalance(positions))

        return anomalies

    def _analyze_force_balance(self, positions: List[dict]) -> dict:
        """分析力量平衡"""
        countries = {}
        for pos in positions:
            country = pos.get("country", "未知")
            if country not in countries:
                countries[country] = {"count": 0, "types": {}}
            countries[country]["count"] += 1
            unit_type = pos.get("unit_type", "unknown")
            countries[country]["types"][unit_type] = countries[country]["types"].get(unit_type, 0) + 1

        return {
            "countries": countries,
            "total_units": len(positions),
            "dominant_country": max(countries.keys(), key=lambda c: countries[c]["count"]) if countries else "未知",
        }

    def _predict_next_moves(self, positions: List[dict], history: List[dict] = None) -> List[str]:
        """预测下一步可能行动（简化版）"""
        moves = []

        # 基于当前位置分析趋势
        force = self._analyze_force_balance(positions)

        # 如果某方力量明显优势，可能采取进攻态势
        if force["total_units"] > 0:
            moves.append("建议加强关键区域监控")

        if history and len(history) >= 2:
            # 基于历史轨迹预测
            moves.append("近期活跃度较高，建议保持警戒")

        moves.append("持续跟踪外交动向")

        return moves

    def _identify_risk_zones(self, positions: List[dict]) -> List[dict]:
        """识别风险区域"""
        risk_zones = []

        # 检查靠近边界的单位
        for pos in positions:
            lat = float(pos.get("latitude", 0) or 0)
            lng = float(pos.get("longitude", 0) or 0)

            # 简化：靠近海岸线视为高风险
            if 20 < lat < 45 and 100 < lng < 130:
                risk_zones.append({
                    "lat": lat,
                    "lng": lng,
                    "level": "中",
                    "reason": "位于争议海域",
                })

        return risk_zones[:5]  # 最多返回5个

    def _generate_recommendations(self, result: dict) -> List[str]:
        """生成建议"""
        recs = []

        if result["force_analysis"].get("dominant_country"):
            recs.append(f"注意{result['force_analysis']['dominant_country']}动向")

        if result["risk_zones"]:
            recs.append(f"关注{len(result['risk_zones'])}个风险区域")

        recs.append("建议启动AI持续监控模式")

        return recs

    def _calculate_damage_coefficients(self, sim_units: List[dict]) -> dict:
        """计算模拟毁伤系数"""
        coefficients = {}

        unit_types = set(u.get("unit_type", "unknown") for u in sim_units)
        for ut in unit_types:
            units = [u for u in sim_units if u.get("unit_type") == ut]
            # 简化：基于单位数量计算
            coefficients[ut] = {
                "avg_damage": 0.6,
                "count": len(units),
                "effectiveness": min(1.0, len(units) * 0.1),
            }

        return coefficients

    def _analyze_weather_impact(self, sim_units: List[dict], weather: dict) -> dict:
        """分析天气对模拟的影响"""
        wind_speed = weather.get("wind_speed", 5)
        visibility = weather.get("visibility", "good")

        impact = {
            "aircraft_penalty": 0.0,
            "naval_penalty": 0.0,
            "ground_penalty": 0.0,
        }

        if wind_speed > 20:
            impact["aircraft_penalty"] = 0.3
            impact["naval_penalty"] = 0.1

        if visibility == "poor":
            impact["aircraft_penalty"] += 0.2

        return impact

    def _compare_forces(self, sim_units: List[dict]) -> dict:
        """力量对比"""
        sides = {}
        for unit in sim_units:
            side = unit.get("side", "unknown")
            if side not in sides:
                sides[side] = {"count": 0, "power": 0}
            sides[side]["count"] += 1
            sides[side]["power"] += unit.get("combat_power", 1)

        return sides

    def _generate_sim_tips(self, result: dict) -> List[str]:
        """生成模拟建议"""
        tips = []

        dc = result.get("damage_coefficients", {})
        if dc:
            strongest = max(dc.items(), key=lambda x: x[1].get("effectiveness", 0))
            tips.append(f"当前最强单位类型: {strongest[0]}")

        wi = result.get("weather_impact", {})
        if wi and any(v > 0 for v in wi.values()):
            tips.append("天气条件不佳，注意调整战术")

        return tips

    def _check_sudden_movement(self, positions: List[dict]) -> List[dict]:
        """检测突然移动"""
        # 简化实现
        return []

    def _check_unusual_concentration(self, positions: List[dict]) -> List[dict]:
        """检测异常集结"""
        anomalies = []

        # 检查同国家/同类型单位密度
        density_threshold = 5  # 简化

        return anomalies

    def _check_force_imbalance(self, positions: List[dict]) -> List[dict]:
        """检测力量失衡"""
        force = self._analyze_force_balance(positions)
        anomalies = []

        countries = force.get("countries", {})
        if len(countries) >= 2:
            counts = list(countries.values())
            max_count = max(c["count"] for c in counts)
            min_count = min(c["count"] for c in counts)
            if max_count > min_count * 3:
                anomalies.append({
                    "type": "force_imbalance",
                    "level": "高",
                    "description": f"力量对比悬殊 ({max_count} vs {min_count})",
                })

        return anomalies
