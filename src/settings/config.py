"""
Config Validator - 配置验证器
"""

import sys
import os
import re
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class ConfigValidator:
    """配置验证器 - 验证各种配置项的有效性"""
    
    @staticmethod
    def validate_feishu(app_id, app_secret):
        """
        验证飞书凭证格式并测试连接
        返回: (success, message)
        """
        if not app_id or not app_secret:
            return False, '飞书 App ID 和 App Secret 不能为空'
        
        # 检查格式
        if not re.match(r'^[a-zA-Z0-9_-]+$', app_id):
            return False, '飞书 App ID 格式无效'
        
        if len(app_secret) < 10:
            return False, '飞书 App Secret 格式无效'
        
        # 测试连接
        try:
            import requests
            url = f'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
            data = {'app_id': app_id, 'app_secret': app_secret}
            resp = requests.post(url, json=data, timeout=10)
            result = resp.json()
            
            if result.get('code') == 0:
                return True, '飞书连接成功'
            else:
                return False, f'飞书认证失败: {result.get("msg", "未知错误")}'
        except ImportError:
            return True, '飞书凭证格式正确 (requests未安装，无法测试连接)'
        except Exception as e:
            return False, f'飞书连接测试失败: {str(e)}'
    
    @staticmethod
    def validate_amap_key(key):
        """
        验证高德地图API Key格式
        返回: (success, message)
        """
        if not key:
            return False, '高德地图 API Key 不能为空'
        
        # 高德API Key通常是32位字母数字组合
        if not re.match(r'^[a-zA-Z0-9]{20,32}$', key):
            return False, '高德地图 API Key 格式无效 (应为20-32位字母数字)'
        
        # 尝试验证
        try:
            url = f'https://restapi.amap.com/v3/config/district?key={key}&keywords=中国&subdistrict=0'
            resp = urllib.request.urlopen(url, timeout=10)
            result = resp.read().decode('utf-8')
            
            if 'status' in result and '1' in result[:20]:
                return True, '高德地图 Key 验证成功'
            else:
                return False, '高德地图 Key 验证失败'
        except Exception as e:
            return True, f'高德地图 Key 格式正确 (无法验证: {str(e)})'
    
    @staticmethod
    def validate_ai_key(key, model='minimax'):
        """
        验证AI API Key
        返回: (success, message)
        """
        if not key:
            return False, 'API Key 不能为空'
        
        if model == 'minimax':
            # MiniMax API Key格式
            if len(key) < 20:
                return False, 'MiniMax API Key 格式无效'
            return True, 'MiniMax API Key 格式正确'
        
        elif model == 'openai':
            # OpenAI API Key格式
            if not key.startswith('sk-'):
                return False, 'OpenAI API Key 应以 sk- 开头'
            if len(key) < 40:
                return False, 'OpenAI API Key 格式无效'
            return True, 'OpenAI API Key 格式正确'
        
        elif model == 'zhipu':
            # 智谱AI
            if len(key) < 20:
                return False, '智谱AI API Key 格式无效'
            return True, '智谱AI API Key 格式正确'
        
        return True, 'API Key 格式正确'
    
    @staticmethod
    def validate_crawler_interval(hours):
        """
        验证爬虫更新频率
        返回: (success, message)
        """
        try:
            hours = int(hours)
            if hours < 1:
                return False, '爬虫频率不能小于1小时'
            if hours > 6:
                return False, '爬虫频率不能大于6小时'
            return True, f'爬虫频率设置有效: {hours}小时'
        except ValueError:
            return False, '爬虫频率必须是1-6之间的数字'
    
    @staticmethod
    def validate_path(path):
        """
        验证路径是否存在或可创建
        返回: (success, message)
        """
        if not path:
            return False, '路径不能为空'
        
        path = os.path.expanduser(path)
        
        if os.path.exists(path):
            if os.access(path, os.W_OK):
                return True, f'路径可用: {path}'
            else:
                return False, f'路径存在但无写入权限: {path}'
        
        # 尝试创建
        try:
            os.makedirs(path, exist_ok=True)
            return True, f'路径已创建: {path}'
        except Exception as e:
            return False, f'无法创建路径: {str(e)}'
    
    @staticmethod
    def validate_threshold(value, min_val=1, max_val=10):
        """
        验证阈值设置
        返回: (success, message)
        """
        try:
            val = float(value)
            if val < min_val or val > max_val:
                return False, f'阈值必须在{min_val}-{max_val}之间'
            return True, f'阈值设置有效: {val}'
        except ValueError:
            return False, '阈值必须是数字'
