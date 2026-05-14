"""飞书通知模块"""
import requests
import os
from typing import Optional

class FeishuNotifier:
    """飞书通知器"""
    
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or os.environ.get("FEISHU_APP_ID", "")
        self.app_secret = app_secret or os.environ.get("FEISHU_APP_SECRET", "")
        self.api_base = "https://open.feishu.cn/open-apis"
    
    def send_text(self, chat_id: str, text: str) -> bool:
        """发送文本消息"""
        if not self.app_id or not self.app_secret:
            print("飞书未配置，跳过通知")
            return False
        
        try:
            # 获取 tenant access token
            token_url = f"{self.api_base}/auth/v3/tenant_access_token/internal"
            token_resp = requests.post(token_url, json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }, timeout=10)
            token_data = token_resp.json()
            access_token = token_data.get("tenant_access_token", "")
            
            if not access_token:
                print("获取 access_token 失败")
                return False
            
            # 发送消息
            msg_url = f"{self.api_base}/im/v1/messages?receive_id_type=chat_id"
            headers = {"Authorization": f"Bearer {access_token}"}
            payload = {
                "receive_id": chat_id,
                "msg_type": "text",
                "content": f"{{\"text\": \"{text}\"}}"
            }
            resp = requests.post(msg_url, headers=headers, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"飞书通知失败: {e}")
            return False
    
    def send_alert(self, title: str, description: str, level: str = "medium") -> bool:
        """发送预警消息"""
        level_emoji = {"low": "🔵", "medium": "🟡", "high": "🟠", "critical": "🔴"}
        emoji = level_emoji.get(level.lower(), "🟡")
        text = f"{emoji} 【预警】{title}\n\n{description}"
        # 发送到默认 chat_id 或环境变量指定的 chat
        chat_id = os.environ.get("FEISHU_ALERT_CHAT_ID", "")
        if chat_id:
            return self.send_text(chat_id, text)
        print(f"预警（未发送到飞书）: {title}")
        return False
