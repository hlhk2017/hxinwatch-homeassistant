"""HXinWatch API客户端。"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)

class HXinWatchAPI:
    """HXinWatch API客户端。"""

    def __init__(
        self, 
        token: str,
        imei: str,
        language: str = "zh-Hans",
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """初始化API客户端。"""
        self._token = token
        self._imei = imei
        self._language = language
        self._session = session or aiohttp.ClientSession()
        self._base_url = "https://yg.hxinwatch.com/sdkapi/api"

    async def async_get_device_status(self) -> Dict[str, Any]:
        """获取设备状态。"""
        url = f"{self._base_url}/related/main"
        payload = {
            "token": self._token,
            "imei": self._imei,
            "language": self._language,
        }
        
        return await self._async_post(url, payload)

    async def async_get_contacts(self) -> List[Dict[str, Any]]:
        """获取通讯录列表。"""
        url = f"{self._base_url}/device/config/contact"
        payload = {
            "token": self._token,
            "imei": self._imei,
            "language": self._language,
        }
        
        response = await self._async_post(url, payload)
        return response.get("data", [])

    async def async_update_contacts(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新通讯录。"""
        url = f"{self._base_url}/device/config/update"
        payload = {
            "contacts": contacts,
            "token": self._token,
            "imei": self._imei,
            "language": self._language,
        }
        
        return await self._async_post(url, payload)

    async def async_get_alarms(self) -> List[Dict[str, Any]]:
        """获取闹钟列表。"""
        url = f"{self._base_url}/device/config/remind"
        payload = {
            "token": self._token,
            "imei": self._imei,
            "language": self._language,
        }
        
        response = await self._async_post(url, payload)
        return response.get("data", [])

    async def async_update_alarms(self, alarms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新闹钟。"""
        url = f"{self._base_url}/device/config/update"
        payload = {
            "reminds": alarms,
            "token": self._token,
            "imei": self._imei,
            "language": self._language,
        }
        
        return await self._async_post(url, payload)

    async def async_get_voice_messages(self) -> List[Dict[str, Any]]:
        """获取语音消息。"""
        url = f"{self._base_url}/chat/chats"
        payload = {
            "token": self._token,
            "imei": self._imei,
            "language": self._language,
        }
        
        response = await self._async_post(url, payload)
        # 只返回接收到的消息(fromme=0)
        return [msg for msg in response.get("data", []) if msg.get("fromme") == 0]

    async def _async_post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送POST请求并处理响应。"""
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json;charset=UTF-8",
        }
        
        try:
            async with self._session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as error:
            _LOGGER.error("Error communicating with HXinWatch API: %s", error)
            raise
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout communicating with HXinWatch API")
            raise    