"""HXinWatch集成的数据协调器。"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HXinWatchAPI
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_coordinator(hass: HomeAssistant, entry: ConfigEntry) -> DataUpdateCoordinator:
    """设置数据协调器。"""
    # 创建API客户端
    api = HXinWatchAPI(
        token=entry.data["token"],
        imei=entry.data["imei"],
        language=entry.data.get("language", "zh-Hans"),
    )
    
    async def async_update_data():
        """获取最新数据。"""
        try:
            # 获取设备状态
            status = await api.async_get_device_status()
            
            # 获取最新语音消息
            voice_messages = await api.async_get_voice_messages()
            
            # 将语音消息添加到状态数据中
            status["voice_messages"] = voice_messages
            
            return status
        except Exception as error:
            raise UpdateFailed(f"更新设备数据失败: {error}") from error
    
    # 创建数据协调器
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.data['imei']}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )
    
    # 立即获取一次数据
    await coordinator.async_config_entry_first_refresh()
    
    return coordinator    