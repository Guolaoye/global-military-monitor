import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .manager import get_settings_manager

class AIModelConfig:
    MODELS = {
        'minimax': {
            'name': 'MiniMax MoE',
            'name_cn': 'MiniMax MoE 大模型',
            'api_format': 'https://api.minimax.chat/v1/text/chatcompletion_v2',
            'param_format': {'model': 'abab6.5s-chat'},
            'default_temp': 0.7
        },
        'openai': {
            'name': 'OpenAI GPT-4',
            'name_cn': 'OpenAI GPT-4',
            'api_format': 'https://api.openai.com/v1/chat/completions',
            'param_format': {'model': 'gpt-4'},
            'default_temp': 0.7
        },
        'zhipu': {
            'name': 'Zhipu GLM-4',
            'name_cn': '智谱 GLM-4',
            'api_format': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            'param_format': {'model': 'glm-4'},
            'default_temp': 0.7
        },
        'dashscope': {
            'name': 'Alibaba DashScope',
            'name_cn': '阿里 通义千问',
            'api_format': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
            'param_format': {'model': 'qwen-plus'},
            'default_temp': 0.7
        }
    }
    
    @staticmethod
    def get_models():
        return AIModelConfig.MODELS
    
    @staticmethod
    def get_model_info(model_name):
        return AIModelConfig.MODELS.get(model_name, {})
    
    @staticmethod
    def test_connection(model, api_key):
        import urllib.request
        import urllib.error
        import json
        
        if not api_key:
            return False, 'API Key 不能为空'
        
        model_info = AIModelConfig.MODELS.get(model, {})
        if not model_info:
            return False, f'不支持的模型: {model}'
        
        try:
            if model == 'minimax':
                url = 'https://api.minimax.chat/v1/text/chatcompletion_v2'
                headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
                data = {'model': 'abab6.5s-chat', 'messages': [{'role': 'user', 'content': '你好'}], 'max_tokens': 10}
            elif model == 'openai':
                url = 'https://api.openai.com/v1/chat/completions'
                headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
                data = {'model': 'gpt-4', 'messages': [{'role': 'user', 'content': '你好'}], 'max_tokens': 10}
            elif model == 'zhipu':
                url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
                headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
                data = {'model': 'glm-4', 'messages': [{'role': 'user', 'content': '你好'}], 'max_tokens': 10}
            elif model == 'dashscope':
                url = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
                headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
                data = {'model': 'qwen-plus', 'messages': [{'role': 'user', 'content': '你好'}], 'max_tokens': 10}
            else:
                return False, f'不支持的模型: {model}'
            
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode('utf-8'))
            
            if 'choices' in result or 'data' in result:
                return True, f'{model_info.get("name_cn", model)} 连接成功'
            else:
                return False, f'API返回异常: {result}'
        except urllib.error.HTTPError as e:
            try:
                error = json.loads(e.read().decode('utf-8'))
                return False, f'HTTP错误 {e.code}: {error.get("error", {}).get("message", str(e))}'
            except:
                return False, f'HTTP错误 {e.code}'
        except Exception as e:
            return False, f'连接失败: {str(e)}'
    
    @staticmethod
    def set_default_model(model):
        mgr = get_settings_manager()
        mgr.save('ai_model', model)
        model_info = AIModelConfig.MODELS.get(model, {})
        if model_info:
            mgr.save('ai_temperature', model_info.get('default_temp', 0.7))
        return True
