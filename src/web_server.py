# -*- coding: utf-8 -*-
"""
全球军事动态分析研判系统 - Web 服务入口
提供浏览器访问界面
"""
import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request

# 确保项目路径可用
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# ================== 页面路由 ==================

@app.route('/')
def index():
    """主界面"""
    return render_template('index.html', 
                         title='全球军事动态分析研判系统',
                         version='V1.0')

@app.route('/situational-real')
def situational_real():
    """真实态势推演"""
    return render_template('situational_real.html', title='真实态势推演')

@app.route('/situational-sim')
def situational_sim():
    """模拟态势推演"""
    return render_template('situational_sim.html', title='模拟态势推演')

@app.route('/threat-alert')
def threat_alert():
    """威胁预警"""
    return render_template('threat_alert.html', title='威胁预警')

@app.route('/ai-chat')
def ai_chat():
    """AI 知识问答"""
    return render_template('ai_chat.html', title='AI 知识问答')

@app.route('/settings')
def settings():
    """系统设置"""
    return render_template('settings.html', title='系统设置')

# ================== API 接口 ==================

@app.route('/api/units')
def get_units():
    """获取所有军事单位"""
    try:
        from src.db.connection import get_cursor
        with get_cursor() as cur:
            cur.execute("""
                SELECT unit_id, name, unit_type, country, 
                       ST_X(location) as lon, ST_Y(location) as lat,
                       status, updated_at
                FROM military_units
                ORDER BY updated_at DESC
                LIMIT 100
            """)
            units = []
            for row in cur.fetchall():
                units.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'country': row[3],
                    'lon': float(row[4]) if row[4] else 0,
                    'lat': float(row[5]) if row[5] else 0,
                    'status': row[6],
                    'updated': row[7].isoformat() if row[7] else None
                })
            return jsonify({'success': True, 'units': units})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/timeline')
def get_timeline():
    """获取时间轴数据"""
    try:
        from src.db.connection import get_cursor
        with get_cursor() as cur:
            cur.execute("""
                SELECT DISTINCT DATE(updated_at) as date, COUNT(*) as count
                FROM military_units
                GROUP BY DATE(updated_at)
                ORDER BY date DESC
                LIMIT 30
            """)
            dates = [{'date': str(r[0]), 'count': r[1]} for r in cur.fetchall()]
            return jsonify({'success': True, 'dates': dates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/affected-units', methods=['POST'])
def get_affected_units():
    """获取受影响单位"""
    try:
        data = request.json
        lon = float(data.get('lon', 0))
        lat = float(data.get('lat', 0))
        radius_km = float(data.get('radius_km', 100))
        
        from src.db.connection import get_cursor
        with get_cursor() as cur:
            cur.execute("""
                SELECT unit_id, name, unit_type, country,
                       ST_X(location) as lon, ST_Y(location) as lat,
                       status
                FROM military_units
                WHERE ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
            """, (lon, lat, radius_km * 1000))
            
            units = []
            for row in cur.fetchall():
                units.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'country': row[3],
                    'lon': float(row[4]) if row[4] else 0,
                    'lat': float(row[5]) if row[5] else 0,
                    'status': row[6]
                })
            return jsonify({'success': True, 'units': units, 'center': {'lon': lon, 'lat': lat}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    """AI 分析接口"""
    try:
        data = request.json
        query = data.get('query', '')
        
        # 导入 AI 引擎
        from src.ai_engine.chat import RAGChat
        chat = RAGChat()
        result = chat.ask(query)
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/threats')
def get_threats():
    """获取威胁预警"""
    try:
        from src.threat_alert.manager import ThreatAlertManager
        manager = ThreatAlertManager()
        # 这里简化处理，实际应该调用检测逻辑
        threats = []
        return jsonify({'success': True, 'threats': threats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings')
def get_settings():
    """获取设置"""
    try:
        from src.settings.manager import SettingsManager
        mgr = SettingsManager()
        return jsonify({'success': True, 'settings': mgr.get_all()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """保存设置"""
    try:
        data = request.json
        from src.settings.manager import SettingsManager
        mgr = SettingsManager()
        mgr.save_all(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sim/start', methods=['POST'])
def start_simulation():
    """启动模拟推演"""
    try:
        from src.situational_sim.engine import SimSituationEngine
        engine = SimSituationEngine()
        engine.start_simulation()
        return jsonify({'success': True, 'message': '模拟推演已启动'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sim/end', methods=['POST'])
def end_simulation():
    """结束模拟推演"""
    try:
        from src.situational_sim.engine import SimSituationEngine
        engine = SimSituationEngine()
        engine.end_simulation()
        return jsonify({'success': True, 'message': '模拟推演已结束，原始数据未受影响'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ================== 健康检查 ==================

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    })

# ================== 启动 ==================

def create_template_folders():
    """创建模板目录"""
    for folder in ['templates', 'static', 'static/css', 'static/js']:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder)
        os.makedirs(path, exist_ok=True)

if __name__ == '__main__':
    create_template_folders()
    print("=" * 50)
    print("全球军事动态分析研判系统 Web 服务")
    print("=" * 50)
    print("访问地址: http://localhost:5000")
    print("局域网访问: http://<Pi的IP>:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
