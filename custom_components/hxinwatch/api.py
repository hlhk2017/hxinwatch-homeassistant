# hxinwatch/api.py
"""HXinWatch API客户端。"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)

class HXinWatchAPI:
    """HXinWatch API客户端。"""

    def __init__(
        self,
        imei: str,
        appid: str, # appid 现在是必需的，用于获取Token
        language: str = "zh-Hans",
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """初始化API客户端。"""
        self._token: Optional[str] = None # Token 将由异步方法获取和管理
        self._imei = imei
        self._appid = appid # 存储 appid
        self._language = language
        self._session = session or aiohttp.ClientSession()
        self._base_url = "https://yg.hxinwatch.com/sdkapi/api"
        self._token_expires_time = 0 # Unix timestamp in milliseconds

    async def async_refresh_token_if_needed(self) -> None:
        """检查Token是否即将过期，如果过期则自动刷新。"""
        # 如果当前没有Token，或者Token即将过期 (例如在过期前5分钟刷新)
        current_time_ms = time.time() * 1000
        # 如果 token 为 None 或 token 已经过期或将在 5 分钟内过期
        if self._token is None or current_time_ms > (self._token_expires_time - 300000): # 300000 ms = 5 minutes
            _LOGGER.info("HXinWatch Token即将过期或不存在，尝试刷新Token。")
            await self.async_get_token_by_appid()

    async def async_get_token_by_appid(self) -> None:
        """通过 appid 接口获取新的Token。"""
        if not self._appid:
            _LOGGER.error("缺少 AppID 参数，无法获取Token。")
            raise Exception("缺少 AppID 参数。")

        url = f"{self._base_url}/wechat/auth"
        # GET 请求的参数
        params = {
            "appid": self._appid,
            "spread": "", # 根据抓包数据，这些字段是空的或 undefined
            "login_type": "",
            "openid": "undefined",
        }

        headers = {
            "Host": "yg.hxinwatch.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; 23049RAD8C Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160117 MMWEBSDK/20250201 MMWEBID/2229 MicroMessenger/8.0.58.2821(0x28003A41) WeChat/arm64 Weixin GPVersion/1 NetType/WIFI Language/zh_CN ABI/arm64",
            "Accept": "*/*",
            "Origin": "http://wx.hxinwatch.com", #
            "X-Requested-With": "com.tencent.mm", #
            "Referer": "http://wx.hxinwatch.com/", #
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7", #
        }

        try:
            _LOGGER.debug("正在通过AppID获取新的Token。URL: %s, Params: %s", url, params)
            async with self._session.get(url, params=params, headers=headers) as response: # 使用 GET 请求
                response.raise_for_status()
                data = await response.json()
                _LOGGER.debug("Token获取接口响应: %s", data)

                if data.get("code") == 200 and "data" in data and "token" in data["data"]:
                    self._token = data["data"]["token"]
                    self._token_expires_time = int(data["data"]["expires_time"])
                    _LOGGER.info("成功获取并更新HXinWatch Token。新Token有效期至: %s",
                                 time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._token_expires_time / 1000)))
                else:
                    _LOGGER.error("通过AppID获取Token失败: %s", data.get("msg", "未知错误"))
                    raise Exception(f"获取Token失败: {data.get('msg', '未知错误')}")
        except aiohttp.ClientError as error:
            _LOGGER.error("与HXinWatch认证API通信错误: %s", error)
            raise
        except asyncio.TimeoutError:
            _LOGGER.error("与HXinWatch认证API通信超时。")
            raise

    # 以下所有业务方法（async_get_device_status, async_get_contacts 等）都保持不变，
    # 它们内部会先调用 async_refresh_token_if_needed，确保Token有效。
    # 唯一需要修改的是 _async_post 中 Authorization header 使用 self._token
    # async_get_device_status, async_get_contacts, async_update_contacts,
    # async_get_alarms, async_update_alarms, async_get_voice_messages 保持不变。

    async def async_get_device_status(self) -> Dict[str, Any]:
        """获取设备状态。"""
        await self.async_refresh_token_if_needed()
        url = f"{self._base_url}/related/main"
        payload = {
            "token": self._token,
            "imei": self._imei,
            "language": self._language,
        }
        return await self._async_post(url, payload)

    async def async_get_contacts(self) -> List[Dict[str, Any]]:
        """获取通讯录列表。"""
        await self.async_refresh_token_if_needed()
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
        await self.async_refresh_token_if_needed()
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
        await self.async_refresh_token_if_needed()
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
        await self.async_refresh_token_if_needed()
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
        await self.async_refresh_token_if_needed()
        url = f"{self._base_url}/chat/chats"
        payload = {
            "token": self._token,
            "imei": self._imei,
            "language": self._language,
        }
        response = await self._async_post(url, payload)
        return [msg for msg in response.get("data", []) if msg.get("fromme") == 0]


    async def _async_post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送POST请求并处理响应。"""
        # 确保 token 存在，因为它可能在 async_refresh_token_if_needed 中被设置为 None
        if self._token is None:
            _LOGGER.error("尝试发送POST请求但Token为None，请检查Token刷新机制。")
            raise Exception("Token不可用。")

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
