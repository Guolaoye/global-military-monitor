"""
情境模拟模块 - Situational Simulation Module
提供完整的战场模拟引擎，数据隔离保护机制
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.situational_sim.engine import SimSituationEngine
from src.situational_sim.unit_manager import SimUnitManager
from src.situational_sim.battle_sim import BattleSimulator
from src.situational_sim.weather_effect import WeatherEffectCalculator
from src.situational_sim.report import SimulationReport

__all__ = [
    'SimSituationEngine',
    'SimUnitManager',
    'BattleSimulator',
    'WeatherEffectCalculator',
    'SimulationReport'
]

__version__ = '1.0.0'