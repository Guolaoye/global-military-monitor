"""AI 快速查询（知识问答）接口"""
import sys
import os
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.ai_engine.rag_retriever import RAGRetriever
from src.ai_engine.minimax_client import MiniMaxClient


class ChatInterface:
    """RAG 问答接口（右下角常驻入口）"""

    def __init__(self, model: str = "mini-max"):
        self.model = model
        self.api_key = ""
        self.rag_retriever = RAGRetriever()
        self.minimax_client = MiniMaxClient()
        self.conversation_history: List[Dict] = []
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            from src.config import load_config
            config = load_config()
            self.api_key = config.get("AI_API_KEY", "")
            model_setting = config.get("AI_MODEL", "mini-max")
            # 映射配置名称到实际API模型
            self.model = self._map_model_name(model_setting)
        except Exception:
            pass

    def _map_model_name(self, config_name: str) -> str:
        """映射配置名称到API模型"""
        mapping = {
            "mini-max": "MiniMax-Text-01",
            "openai": "gpt-4o-mini",
            "zhipu": "glm-4-flash",
            "qwen": "qwen-turbo",
        }
        return mapping.get(config_name.lower(), "MiniMax-Text-01")

    def set_model(self, model_name: str, api_key: str = None):
        """切换AI模型"""
        self.model = self._map_model_name(model_name)
        if api_key:
            self.api_key = api_key
        self.minimax_client.set_api_key(self.api_key)

    def chat(self, message: str, history: List[Dict] = None) -> str:
        """
        RAG 问答核心流程

        Args:
            message: 用户消息
            history: 对话历史（可选）

        Returns:
            str: AI 回复文本
        """
        # 1. RAG 检索
        context = self.rag_retriever.build_context(message)

        # 2. 构建消息
        messages = self._build_messages(message, context, history or self.conversation_history)

        # 3. 调用 LLM
        response = self._call_llm(messages)

        # 4. 保存历史
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})

        # 5. 保存到 Obsidian
        self.save_to_obsidian(message, response)

        return response

    def _build_messages(self, message: str, context: str, history: List[Dict]) -> List[Dict]:
        """构建消息列表"""
        system_prompt = f"""你是一个专业的军事情报分析助手。

【背景信息】
{context}

【工作要求】
1. 基于提供的背景信息回答问题
2. 如背景信息不足以回答，明确指出
3. 保持专业、客观的分析风格
4. 涉及军事行动的分析要谨慎、保守

请根据以上背景信息回答用户问题。"""

        messages = [{"role": "system", "content": system_prompt}]

        # 添加历史对话
        for msg in history[-10:]:  # 最多10条历史
            messages.append(msg)

        # 添加当前消息
        messages.append({"role": "user", "content": message})

        return messages

    def _call_llm(self, messages: List[Dict]) -> str:
        """调用 LLM（MiniMax 或 OpenAI）"""
        if not self.api_key:
            return self._mock_response(messages[-1]["content"])

        try:
            if "MiniMax" in self.model:
                return self.minimax_client.chat(messages, model=self.model)
            else:
                # OpenAI 兼容格式
                return self._call_openai(messages)
        except Exception as e:
            return f"AI 服务调用失败: {e}\n请检查 API Key 配置。"

    def _call_openai(self, messages: List[Dict]) -> str:
        """调用 OpenAI 兼容 API"""
        import requests

        # 统一使用 MiniMax 客户端的 call_openai 方法
        return self.minimax_client.call_openai(messages, model=self.model)

    def _mock_response(self, query: str) -> str:
        """Mock 回复（无 API Key 时）"""
        return f"【提示】当前未配置 AI API Key，无法生成分析回复。\n\n您的问题: {query}\n\n请前往【设置】→【AI模型】配置 API Key 后再试。"

    def save_to_obsidian(self, query: str, response: str):
        """保存查询历史到 Obsidian"""
        try:
            from src.obsidian.sync import ObsidianSync

            config = {}
            try:
                from src.config import load_config
                config = load_config()
            except Exception:
                pass

            obsidian_path = config.get("OBSIDIAN_PATH", os.path.expanduser("~/Documents/军事知识库"))
            sync = ObsidianSync(obsidian_path)

            intel_data = {
                "unit_uuid": f"chat_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": f"AI查询记录 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "content": f"**问:** {query}\n\n**答:** {response}",
                "source": "ai_chat",
                "created_at": datetime.now().isoformat(),
                "intel_type": "chat_query",
            }

            sync.sync_intelligence(intel_data)
        except Exception as e:
            print(f"保存到 Obsidian 失败: {e}")

    def get_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
