"""MiniMax API 客户端"""
import sys
import os
import json
import hashlib
from typing import List, Dict, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)


class MiniMaxClient:
    """MiniMax MoE API 客户端"""

    def __init__(self):
        self.api_key = ""
        self.base_url = "https://api.minimax.chat/v1"
        self.model = "MiniMax-Text-01"

    def set_api_key(self, api_key: str):
        """设置 API Key"""
        self.api_key = api_key

    def set_model(self, model: str):
        """设置模型"""
        self.model = model

    def chat(self, messages: List[Dict], model: str = None) -> str:
        """
        调用 MiniMax 聊天 API

        Args:
            messages: 消息列表 [{"role": "system"|"user"|"assistant", "content": "..."}]
            model: 模型名称

        Returns:
            str: AI 回复文本
        """
        if not self.api_key:
            return self._mock_response()

        if model:
            self.model = model

        try:
            import requests

            url = f"{self.base_url}/text/chatcompletion_v2"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000,
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "AI 返回格式异常"

        except ImportError:
            return self._mock_response()
        except Exception as e:
            return f"MiniMax API 调用失败: {e}\n请检查 API Key 和网络连接。"

    def call_openai(self, messages: List[Dict], model: str = None) -> str:
        """
        调用 OpenAI 兼容 API（用于切换到 GPT 等）

        Args:
            messages: 消息列表
            model: 模型名称

        Returns:
            str: AI 回复
        """
        if not self.api_key:
            return self._mock_response()

        try:
            import requests

            url = "https://api.openai.com/v1/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model or "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000,
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "API 返回格式异常"

        except ImportError:
            return self._mock_response()
        except Exception as e:
            return f"API 调用失败: {e}"

    def embed(self, text: str) -> List[float]:
        """
        文本 embedding（简化版：使用 hash + 归一化）

        Args:
            text: 输入文本

        Returns:
            List[float]: embedding 向量
        """
        # 简化实现：使用 hash 生成伪向量
        hash_val = hashlib.md5(text.encode()).digest()
        vec = [b / 255.0 for b in hash_val]

        # 补齐到固定维度 (32维)
        while len(vec) < 32:
            vec.append(0.0)

        return vec[:32]

    def _mock_response(self) -> str:
        """Mock 回复（无 API 时）"""
        return "【提示】当前未配置 AI API Key，请前往【设置】→【AI模型】配置后再使用。"
