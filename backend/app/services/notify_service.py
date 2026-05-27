import json
import hashlib
import hmac
import base64
import time
from typing import Optional

import requests

from app.db.monitor_dao import NotifyChannelDAO
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NotifyService:

    @staticmethod
    def send_to_channel(channel_id: int, title: str, content: str) -> bool:
        channel = NotifyChannelDAO.get_by_id(channel_id)
        if not channel or not channel.enabled:
            logger.info(f"通知渠道 {channel_id} 不存在或已禁用")
            return False

        handler_map = {
            "feishu": NotifyService._send_feishu,
            "wechat_work": NotifyService._send_wechat_work,
            "dingtalk": NotifyService._send_dingtalk,
            "custom": NotifyService._send_custom,
        }

        handler = handler_map.get(channel.channel_type)
        if not handler:
            logger.warning(f"不支持的通知渠道类型: {channel.channel_type}")
            return False

        try:
            result = handler(channel, title, content)
            logger.info(f"通知发送成功: channel={channel.channel_type}, name={channel.name}")
            return result
        except Exception as e:
            logger.error(f"通知发送失败: channel={channel.channel_type}, error={e}")
            return False

    @staticmethod
    def notify_digest(digest_date: str, title: str, content: str, video_count: int):
        channels = NotifyChannelDAO.get_enabled()
        for ch in channels:
            if ch.notify_on_digest:
                short_content = content[:2000] if len(content) > 2000 else content
                NotifyService.send_to_channel(ch.id, title, short_content)

    @staticmethod
    def notify_new_favorite(platform: str, title: str, url: str):
        channels = NotifyChannelDAO.get_enabled()
        for ch in channels:
            if ch.notify_on_new_favorite:
                msg = f"新增收藏视频\n平台: {platform}\n标题: {title}\n链接: {url}"
                NotifyService.send_to_channel(ch.id, "📥 新增收藏视频", msg)

    @staticmethod
    def notify_error(error_msg: str):
        channels = NotifyChannelDAO.get_enabled()
        for ch in channels:
            if ch.notify_on_error:
                NotifyService.send_to_channel(ch.id, "⚠️ 收藏监控异常", error_msg)

    @staticmethod
    def _send_feishu(channel, title: str, content: str) -> bool:
        url = channel.webhook_url
        secret = channel.secret

        headers = {"Content-Type": "application/json"}

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title,
                    },
                    "template": "blue",
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": content,
                    }
                ],
            },
        }

        if secret:
            timestamp = str(int(time.time()))
            string_to_sign = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            sign = base64.b64encode(hmac_code).decode("utf-8")
            payload["timestamp"] = timestamp
            payload["sign"] = sign

        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") != 0:
            logger.warning(f"飞书通知失败: {data.get('msg')}")
            return False
        return True

    @staticmethod
    def _send_wechat_work(channel, title: str, content: str) -> bool:
        url = channel.webhook_url

        headers = {"Content-Type": "application/json"}

        markdown_content = f"### {title}\n\n{content}"

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": markdown_content,
            },
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        data = resp.json()
        if data.get("errcode") != 0:
            logger.warning(f"企业微信通知失败: {data.get('errmsg')}")
            return False
        return True

    @staticmethod
    def _send_dingtalk(channel, title: str, content: str) -> bool:
        url = channel.webhook_url
        secret = channel.secret

        if secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(
                secret.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            sign = base64.b64encode(hmac_code).decode("utf-8")
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        headers = {"Content-Type": "application/json"}

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"### {title}\n\n{content}",
            },
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        data = resp.json()
        if data.get("errcode") != 0:
            logger.warning(f"钉钉通知失败: {data.get('errmsg')}")
            return False
        return True

    @staticmethod
    def _send_custom(channel, title: str, content: str) -> bool:
        url = channel.webhook_url

        headers = {"Content-Type": "application/json"}

        payload = {
            "title": title,
            "content": content,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        return resp.status_code == 200

    @staticmethod
    def test_channel(channel_id: int) -> dict:
        channel = NotifyChannelDAO.get_by_id(channel_id)
        if not channel:
            return {"success": False, "message": "通知渠道不存在"}

        try:
            result = NotifyService.send_to_channel(
                channel_id,
                "🔔 BiliNote 通知测试",
                "这是一条来自 BiliNote 的测试通知，如果你收到了说明配置正确！",
            )
            return {
                "success": result,
                "message": "测试通知发送成功" if result else "测试通知发送失败",
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
