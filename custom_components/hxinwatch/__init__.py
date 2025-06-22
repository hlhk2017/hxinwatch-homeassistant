"""支持HXinWatch设备的集成。"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers import discovery

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .api import HXinWatchAPI
from . import services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置HXinWatch设备的配置入口。"""
    _LOGGER.debug("Async setup entry started for HXinWatch (Entry ID: %s).", entry.entry_id)
    token = entry.data["token"]
    imei = entry.data["imei"]
    language = entry.data.get("language", "zh-Hans")
    
    # 获取用户配置的刷新间隔，它现在应该是一个整数
    scan_interval_seconds = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL) # 它现在总是整数
    
    _LOGGER.debug("刷新间隔设置为: %s 秒", scan_interval_seconds)
    
    try:
        session = async_get_clientsession(hass)
        api = HXinWatchAPI(token, imei, language, session)
        _LOGGER.debug("HXinWatchAPI 实例已创建。")
    except Exception as e:
        _LOGGER.error("创建 HXinWatchAPI 实例失败: %s", e)
        return False

    async def async_update_data():
        """获取最新数据的函数。"""
        try:
            _LOGGER.debug("开始从HXinWatch API获取设备状态...")
            status = await api.async_get_device_status()
            _LOGGER.debug("从HXinWatch API获取到设备状态: %s", status)
            
            _LOGGER.debug("开始从HXinWatch API获取语音消息...")
            voice_messages = await api.async_get_voice_messages()
            _LOGGER.debug("从HXinWatch API获取到语音消息: %s", voice_messages)

            _LOGGER.debug("开始从HXinWatch API获取通讯录...")
            contacts = await api.async_get_contacts()
            _LOGGER.debug("从HXinWatch API获取到通讯录: %s", contacts)

            _LOGGER.debug("开始从HXinWatch API获取闹钟...")
            alarms = await api.async_get_alarms()
            _LOGGER.debug("从HXinWatch API获取到闹钟: %s", alarms)
            
            full_data = status.get("data", {})
            full_data["voice_messages"] = voice_messages
            full_data["contacts"] = contacts
            full_data["alarms"] = alarms
            
            return {
                "msg": status.get("msg"),
                "code": status.get("code"),
                "data": full_data,
            }
        except Exception as error:
            _LOGGER.error("获取设备数据失败: %s", error)
            raise UpdateFailed(f"获取设备数据失败: {error}") from error
    
    try:
        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data['imei']}",
            update_method=async_update_data,
            update_interval=timedelta(seconds=scan_interval_seconds), # 使用整数秒数
        )
        _LOGGER.debug("DataUpdateCoordinator 实例已创建。")
    except Exception as e:
        _LOGGER.error("创建 DataUpdateCoordinator 实例失败: %s", e)
        return False
    
    _LOGGER.debug("首次加载HXinWatch设备数据...")
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("HXinWatch协调器首次刷新完成，数据: %s", coordinator.data)
    except Exception as e:
        _LOGGER.error("协调器首次刷新失败: %s", e)
        return False
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }
    _LOGGER.debug("协调器和 API 已存储在 hass.data 中。")
    
    _LOGGER.debug("转发平台设置: %s", PLATFORMS)
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.debug("平台设置转发成功。")
    except Exception as e:
        _LOGGER.error("平台设置转发失败: %s", e)
        return False

    _LOGGER.debug("加载通知平台。")
    try:
        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                Platform.NOTIFY,
                DOMAIN,
                {"entry_id": entry.entry_id},
                entry,
            )
        )
        _LOGGER.debug("通知平台加载任务已创建。")
    except Exception as e:
        _LOGGER.error("通知平台加载失败: %s", e)
        # 通知平台加载失败不应该阻止主集成加载，但仍需记录

    _LOGGER.debug("设置 HXinWatch 服务。")
    try:
        await services.async_setup_services(hass)
        _LOGGER.debug("HXinWatch 服务设置成功。")
    except Exception as e:
        _LOGGER.error("服务注册失败: %s", e)
        return False

    _LOGGER.debug("Async setup entry 完成成功。")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置入口。"""
    _LOGGER.debug("Async unload entry started for HXinWatch (Entry ID: %s).", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("HXinWatch 集成数据已从 hass.data 中移除。")
    
    _LOGGER.debug("Async unload entry 完成，卸载状态: %s", unload_ok)
    return unload_ok