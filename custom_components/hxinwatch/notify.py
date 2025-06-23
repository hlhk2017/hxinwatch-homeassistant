# hxinwatch/notify.py
"""支持HXinWatch设备的通知平台。"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.notify import (
    ATTR_DATA,
    BaseNotificationService,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .api import HXinWatchAPI

_LOGGER = logging.getLogger(__name__)

async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> BaseNotificationService | None:
    """获取HXinWatch通知服务。"""
    if discovery_info is None or "entry_id" not in discovery_info:
        _LOGGER.error("无法获取配置入口ID，无法设置通知服务。")
        return None
    
    entry_id = discovery_info["entry_id"]
    entry = hass.config_entries.async_get_entry(entry_id)
    
    if not entry:
        _LOGGER.error(f"找不到ID为 {entry_id} 的配置入口，无法设置通知服务。")
        return None

    # 获取配置中的参数
    imei = entry.data["imei"]
    appid = entry.data["appid"] # 新增 appid 参数
    language = entry.data.get("language", "zh-Hans")

    session = async_get_clientsession(hass) 
    
    # HXinWatchAPI 实例化时传入 appid
    api = HXinWatchAPI(
        imei=imei,
        appid=appid,
        language=language,
        session=session,
    )
    
    return HXinWatchNotificationService(api)


class HXinWatchNotificationService(BaseNotificationService):
    """HXinWatch通知服务。"""

    def __init__(self, api) -> None:
        """初始化服务。"""
        self.api = api

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """发送消息。"""
        data = kwargs.get(ATTR_DATA) or {}
        
        _LOGGER.info("Sending message: %s with data: %s", message, data)
        
        # 实际实现中应替换为真实的API调用
        # await self.api.async_send_message(message, data)
