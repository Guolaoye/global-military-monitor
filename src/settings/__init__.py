"""
Settings module for Global Military Monitor System
全球军事动态分析研判系统 - 设置模块
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .manager import SettingsManager
from .config import ConfigValidator
from .widget import SettingsWidget

__all__ = ['SettingsManager', 'ConfigValidator', 'SettingsWidget']
