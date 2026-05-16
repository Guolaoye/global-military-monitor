# -*- coding: utf-8 -*-
"""
实时态势分析视图 - PyQt5主界面组件
提供地图可视化、时间轴控制、影响范围分析、AI辅助分析功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QTextEdit, QSplitter, QGroupBox, QProgressBar
)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal
from PyQt5.QtGui import QFont

from src.db.connection import get_cursor
from src.situational_real.timeline import TimelineManager, PositionHistoryManager
from src.situational_real.affected_units import AffectedUnitsAnalyzer
from src.situational_real.terrain_analysis import TerrainAnalysis
from src.situational_real.ai_assistant import AIAssistant


class RealSituationView(QWidget):
    """
    实时态势分析主视图
    集成地图显示、时间轴、影响单位分析、AI辅助决策
    """
    
    # 自定义信号：地图点击事件
    map_clicked = pyqtSignal(float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timeline_manager = TimelineManager()
        self.position_history_manager = PositionHistoryManager()
        self.affected_analyzer = AffectedUnitsAnalyzer()
        self.terrain_analyzer = TerrainAnalysis()
        self.ai_assistant = AIAssistant()
        
        # 当前时间快照
        self.current_timestamp = datetime.now()
        self.current_positions = []
        
        # 初始化UI
        self.init_ui()
        
        # 加载初始数据
        self.load_current_situation()
    
    def init_ui(self):
        """初始化用户界面布局"""
        main_layout = QVBoxLayout()
        
        # 顶部标题栏
        header_layout = QHBoxLayout()
        title_label = QLabel("【实时态势分析】")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("状态: 就绪")
        header_layout.addWidget(self.status_label)
        
        main_layout.addLayout(header_layout)
        
        # 时间轴控制区域
        timeline_group = self._create_timeline_control()
        main_layout.addWidget(timeline_group)
        
        # 主内容区域：左右分栏
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：地图区域（简化显示）
        map_group = self._create_map_area()
        content_splitter.addWidget(map_group)
        
        # 右侧：分析结果面板
        analysis_group = self._create_analysis_panel()
        content_splitter.addWidget(analysis_group)
        
        content_splitter.setStretchFactor(0, 3)
        content_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(content_splitter)
        
        # 底部操作按钮
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新数据")
        self.refresh_btn.clicked.connect(self.load_current_situation)
        button_layout.addWidget(self.refresh_btn)
        
        self.analyze_btn = QPushButton("AI态势分析")
        self.analyze_btn.clicked.connect(self.perform_ai_analysis)
        button_layout.addWidget(self.analyze_btn)
        
        self.export_btn = QPushButton("导出时间线")
        self.export_btn.clicked.connect(self.export_timeline)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def _create_timeline_control(self):
        """创建时间轴控制组件"""
        group = QGroupBox("时间轴控制")
        layout = QVBoxLayout()
        
        # 时间显示
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("当前时间点:"))
        self.time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # 时间滑块
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("历史时间:"))
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.setValue(100)
        self.timeline_slider.setTickPosition(QSlider.TicksBelow)
        self.timeline_slider.setTickInterval(10)
        self.timeline_slider.valueChanged.connect(self.on_timeline_changed)
        slider_layout.addWidget(self.timeline_slider)
        
        # 时间范围标签
        self.range_label = QLabel("加载中...")
        slider_layout.addWidget(self.range_label)
        
        layout.addLayout(slider_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_map_area(self):
        """创建地图显示区域（简化实现）"""
        group = QGroupBox("态势地图")
        layout = QVBoxLayout()
        
        # 地图点击提示标签
        map_label = QLabel("【地图区域】\n\n点击地图选择分析点\n显示单位位置和影响范围\n\n(实际应用中集成地图组件)")
        map_label.setAlignment(Qt.AlignCenter)
        map_label.setStyleSheet("border: 1px solid #ccc; background: #f5f5f5; padding: 50px;")
        map_label.setMinimumHeight(300)
        
        # 地图点击事件（模拟）
        map_label.mousePressEvent = lambda e: self.on_map_click(0, 0)  # 模拟点击
        
        layout.addWidget(map_label)
        
        # 单位位置列表
        units_label = QLabel("当前可见单位:")
        layout.addWidget(units_label)
        
        self.units_text = QTextEdit()
        self.units_text.setMaximumHeight(150)
        self.units_text.setReadOnly(True)
        layout.addWidget(self.units_text)
        
        group.setLayout(layout)
        return group
    
    def _create_analysis_panel(self):
        """创建分析结果面板"""
        group = QGroupBox("分析结果")
        layout = QVBoxLayout()
        
        # 影响单位分析
        affected_label = QLabel("【影响范围分析】")
        layout.addWidget(affected_label)
        
        self.affected_text = QTextEdit()
        self.affected_text.setReadOnly(True)
        layout.addWidget(self.affected_text)
        
        # 地形天气分析
        terrain_label = QLabel("【地形天气分析】")
        layout.addWidget(terrain_label)
        
        self.terrain_text = QTextEdit()
        self.terrain_text.setReadOnly(True)
        self.terrain_text.setMaximumHeight(120)
        layout.addWidget(self.terrain_text)
        
        # AI分析结果
        ai_label = QLabel("【AI态势研判】")
        layout.addWidget(ai_label)
        
        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setMinimumHeight(150)
        layout.addWidget(self.ai_text)
        
        # AI分析进度条
        self.ai_progress = QProgressBar()
        self.ai_progress.setVisible(False)
        layout.addWidget(self.ai_progress)
        
        group.setLayout(layout)
        return group
    
    def load_current_situation(self):
        """加载当前态势数据"""
        try:
            self.status_label.setText("状态: 加载中...")
            
            # 加载当前位置数据
            self.current_positions = self.timeline_manager.load_positions()
            
            # 加载时间范围
            if self.current_positions:
                self.range_label.setText(
                    f"从 {self.current_positions[0]['reported_at']} 到 {self.current_positions[-1]['reported_at']}"
                )
            
            # 更新单位列表显示
            self.update_units_display()
            
            self.status_label.setText(f"状态: 已加载 {len(self.current_positions)} 条位置记录")
            
        except Exception as e:
            self.status_label.setText(f"状态: 加载失败 - {str(e)}")
            print(f"加载态势数据失败: {e}")
    
    def update_units_display(self):
        """更新单位列表显示"""
        if not self.current_positions:
            self.units_text.setText("暂无单位数据")
            return
        
        display_text = "当前可见单位列表:\n"
        display_text += "-" * 40 + "\n"
        
        # 按单位分组显示
        units_seen = set()
        for pos in self.current_positions[-50:]:  # 显示最近50条
            unit_id = pos.get('unit_id', 'N/A')
            if unit_id not in units_seen:
                units_seen.add(unit_id)
                unit_name = pos.get('unit_name', '未知单位')
                unit_type = pos.get('unit_type', '未知类型')
                lat = pos.get('latitude', 0)
                lng = pos.get('longitude', 0)
                display_text += f"• {unit_name} ({unit_type})\n"
                display_text += f"  位置: {lat:.4f}, {lng:.4f}\n"
        
        self.units_text.setText(display_text)
    
    def on_timeline_changed(self, value):
        """时间轴滑动事件处理"""
        if not self.current_positions:
            return
        
        # 根据滑块值计算对应的时间点
        total = len(self.current_positions)
        index = int(value / 100 * (total - 1))
        index = max(0, min(index, total - 1))
        
        # 获取该时间点的位置快照
        snapshot_time = self.current_positions[index]['reported_at']
        snapshot = self.timeline_manager.get_positions_at_time(snapshot_time)
        
        self.current_timestamp = datetime.fromisoformat(snapshot_time.replace('Z', '+00:00'))
        self.time_label.setText(self.current_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        
        # 更新显示
        display_text = f"时间点: {snapshot_time}\n"
        display_text += f"单位数量: {len(snapshot)}\n"
        for pos in snapshot[:10]:  # 显示前10个
            display_text += f"• {pos.get('unit_name', '未知')} @ ({pos.get('latitude', 0):.4f}, {pos.get('longitude', 0):.4f})\n"
        
        self.units_text.setText(display_text)
    
    def on_map_click(self, lat, lng):
        """地图点击事件处理 - 分析指定点的受影响单位"""
        try:
            # 如果是模拟点击，使用随机坐标
            if lat == 0 and lng == 0:
                import random
                lat = random.uniform(20, 50)
                lng = random.uniform(100, 130)
            
            self.status_label.setText(f"状态: 分析坐标 ({lat:.4f}, {lng:.4f})")
            
            # 分析影响范围内的单位
            affected = self.affected_analyzer.analyze_point(lat, lng)
            
            # 显示影响单位分析结果
            affected_text = f"坐标点 ({lat:.4f}, {lng:.4f}) 影响分析:\n"
            affected_text += "=" * 40 + "\n"
            
            if not affected:
                affected_text += "该点附近无可影响单位\n"
            else:
                affected_text += f"共发现 {len(affected)} 个单位:\n\n"
                
                # 按类型分组
                aircraft = [u for u in affected if u.get('unit_type', '').lower() in ['aircraft', 'air', '飞机']]
                artillery = [u for u in affected if u.get('unit_type', '').lower() in ['artillery', 'missile', '火炮', '导弹']]
                other = [u for u in affected if u not in aircraft and u not in artillery]
                
                if aircraft:
                    affected_text += f"【空中单位】({len(aircraft)})"
                    for u in aircraft[:5]:
                        affected_text += f"\n  • {u['unit_name']} - 距离:{u['distance_km']:.1f}km - 飞行半径:{u.get('flight_range', 'N/A')}km"
                
                if artillery:
                    affected_text += f"\n\n【地面火力单位】({len(artillery)})"
                    for u in artillery[:5]:
                        affected_text += f"\n  • {u['unit_name']} - 距离:{u['distance_km']:.1f}km - 射程:{u.get('weapon_range', 'N/A')}km"
                
                if other:
                    affected_text += f"\n\n【其他单位】({len(other)})"
                    for u in other[:5]:
                        affected_text += f"\n  • {u['unit_name']} - 距离:{u['distance_km']:.1f}km"
            
            self.affected_text.setText(affected_text)
            
            # 地形天气分析
            terrain_result = self.terrain_analyzer.combined_analysis(lat, lng, affected)
            
            terrain_text = f"坐标 ({lat:.4f}, {lng:.4f}) 综合分析:\n"
            terrain_text += "-" * 40 + "\n"
            terrain_text += f"地形评分: {terrain_result.get('terrain_score', 0):.1f}/100\n"
            terrain_text += f"防御加成: {terrain_result.get('defense_bonus', 0):.1f}%"
            terrain_text += f"  机动难度: {terrain_result.get('mobility_factor', 0):.1f}\n\n"
            terrain_text += f"天气影响: {terrain_result.get('weather_impact', '未知')}\n"
            terrain_text += f"能见度: {terrain_result.get('visibility', '未知')}\n"
            terrain_text += f"推荐行动: {terrain_result.get('recommendation', '暂无建议')}\n"
            
            self.terrain_text.setText(terrain_text)
            
            self.status_label.setText("状态: 分析完成")
            
        except Exception as e:
            self.status_label.setText(f"状态: 分析失败 - {str(e)}")
            print(f"地图点击分析失败: {e}")
    
    def perform_ai_analysis(self):
        """执行AI态势分析"""
        try:
            self.status_label.setText("状态: AI分析中...")
            self.ai_progress.setVisible(True)
            self.ai_progress.setRange(0, 0)  # 不确定模式
            
            # 准备分析数据
            positions_summary = []
            for pos in self.current_positions[-20:]:
                positions_summary.append({
                    'unit_name': pos.get('unit_name', '未知'),
                    'latitude': pos.get('latitude', 0),
                    'longitude': pos.get('longitude', 0),
                    'timestamp': pos.get('reported_at', '')
                })
            
            # 调用AI分析
            result = self.ai_assistant.analyze_situation(positions_summary, 'situational_analysis')
            
            # 显示AI分析结果
            ai_text = "【AI态势分析报告】\n"
            ai_text += "=" * 50 + "\n\n"
            
            if result.get('terrain_analysis'):
                ai_text += f"【地形分析】\n{result['terrain_analysis']}\n\n"
            
            if result.get('weather_impact'):
                ai_text += f"【气象影响】\n{result['weather_impact']}\n\n"
            
            if result.get('threat_assessment'):
                ai_text += f"【威胁评估】\n{result['threat_assessment']}\n\n"
            
            if result.get('recommendation'):
                ai_text += f"【行动建议】\n{result['recommendation']}\n"
            
            self.ai_text.setText(ai_text)
            
            self.ai_progress.setVisible(False)
            self.status_label.setText("状态: AI分析完成")
            
        except Exception as e:
            self.ai_progress.setVisible(False)
            self.status_label.setText(f"状态: AI分析失败 - {str(e)}")
            self.ai_text.setText(f"AI分析失败:\n{str(e)}")
            print(f"AI分析失败: {e}")
    
    def export_timeline(self):
        """导出时间线数据"""
        try:
            timeline_data = self.timeline_manager.export_timeline_json()
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"timeline_export_{timestamp}.json"
            
            # 保存到项目目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            filepath = os.path.join(project_root, filename)
            
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, ensure_ascii=False, indent=2)
            
            self.status_label.setText(f"状态: 已导出 {filename}")
            
        except Exception as e:
            self.status_label.setText(f"状态: 导出失败 - {str(e)}")
            print(f"导出时间线失败: {e}")


if __name__ == '__main__':
    # 独立测试
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = RealSituationView()
    window.setWindowTitle("实时态势分析")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
