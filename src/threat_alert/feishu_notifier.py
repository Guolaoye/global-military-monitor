import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
import urllib.request
import urllib.error

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.threat_alert.feishu_card import build_alert_card, build_alert_message
from src.config import load_config


class FeishuNotifier:
    """飞书通知器"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.config = load_config()
        self.webhook_url = webhook_url or self.config.get("FEISHU_WEBHOOK_URL")
        self.app_id = self.config.get("FEISHU_APP_ID")
        self.app_secret = self.config.get("FEISHU_APP_SECRET")
        self._tenant_access_token: Optional[str] = None
    
    def _get_tenant_token(self) -> Optional[str]:
        """获取tenant access token"""
        if self._tenant_access_token:
            return self._tenant_access_token
        
        if not self.app_id or not self.app_secret:
            return None
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = json.dumps({
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }).encode("utf-8")
        
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result.get("code") == 0:
                    self._tenant_access_token = result.get("tenant_access_token")
                    return self._tenant_access_token
        except Exception:
            pass
        return None
    
    def send_alert(
        self,
        alert_data: Dict[str, Any],
        use_card: bool = True
    ) -> bool:
        """
        发送告警通知
        
        Args:
            alert_data: 告警数据，包含 level, title, description, lat, lng
            use_card: 是否使用卡片格式
        
        Returns:
            是否发送成功
        """
        level = alert_data.get("level", "中")
        title = alert_data.get("title", "")
        description = alert_data.get("description", "")
        lat = alert_data.get("latitude")
        lng = alert_data.get("longitude")
        
        # 优先使用卡片格式
        if use_card and self._get_tenant_token():
            return self._send_card(level, title, description, lat, lng)
        elif self.webhook_url:
            return self._send_webhook(level, title, description)
        else:
            # 打印到控制台作为后备
            print(f"[FeishuNotifier] 告警: 【{level}】{title}")
            print(f"  {description}")
            return True
    
    def _send_card(
        self,
        level: str,
        title: str,
        description: str,
        lat: Optional[float],
        lng: Optional[float]
    ) -> bool:
        """使用卡片API发送"""
        token = self._get_tenant_token()
        if not token:
            return False
        
        card = build_alert_card(level, title, description, lat, lng)
        
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        # 默认发到测试群，需要配置具体接收人
        params = "?receive_id_type=chat_id"
        
        payload = {
            "receive_id": self.config.get("FEISHU_CHAT_ID", ""),
            "msg_type": "interactive",
            "content": json.dumps(card)
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url + params,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("code") == 0
        except Exception:
            return False
    
    def _send_webhook(
        self,
        level: str,
        title: str,
        description: str
    ) -> bool:
        """使用webhook发送"""
        message = build_alert_message(level, title, description)
        
        payload = json.dumps({
            "msg_type": "text",
            "content": {"text": message}
        }).encode("utf-8")
        
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("code") == 0
        except Exception:
            return False
