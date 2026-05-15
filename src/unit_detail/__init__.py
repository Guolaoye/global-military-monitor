"""Unit detail view — full unit info page"""
from .views import UnitDetailView, build_unit_detail_from_db
from .mode_switcher import ViewModeSwitcher

__all__ = ["UnitDetailView", "build_unit_detail_from_db", "ViewModeSwitcher"]
