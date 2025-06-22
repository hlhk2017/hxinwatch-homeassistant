# hxinwatch/device_tracker.py
"""支持HXinWatch设备的设备追踪器平台。"""
from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置配置入口的设备追踪器实体。"""
    integration_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = integration_data["coordinator"]
    
    async_add_entities([HXinWatchDeviceTracker(coordinator, entry.unique_id)])


class HXinWatchDeviceTracker(CoordinatorEntity, TrackerEntity):
    """表示HXinWatch设备追踪器的实体。"""

    _attr_has_entity_name = True
    _attr_name = "华芯沃设备位置" # 汉化此名称

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str | None,
    ) -> None:
        """初始化HXinWatch设备追踪器。"""
        super().__init__(coordinator)
        self._attr_unique_id = f"{device_id}_location"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": "华芯沃设备", # 修改这里
            "manufacturer": "华芯沃", # 修改这里
            "model": "Smart Watch",
        }

    @property
    def source_type(self) -> SourceType:
        """返回设备追踪器的源类型。"""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """返回设备的纬度。"""
        data = self.coordinator.data.get("data", {})
        lat = data.get("location", {}).get("latitude")
        _LOGGER.debug("设备追踪器纬度: %s, 原始数据: %s", lat, data)
        return lat

    @property
    def longitude(self) -> float | None:
        """返回设备的经度。"""
        data = self.coordinator.data.get("data", {})
        lon = data.get("location", {}).get("longitude")
        _LOGGER.debug("设备追踪器经度: %s, 原始数据: %s", lon, data)
        return lon

    @property
    def name(self) -> str | None:
        """返回设备的名称。（这里将使用API返回的设备名称，如“安安”）"""
        data = self.coordinator.data.get("data", {})
        name = data.get("info", {}).get("name")
        _LOGGER.debug("设备追踪器名称: %s, 原始数据: %s", name, data)
        return name

    @property
    def location_name(self) -> str | None:
        """返回设备的位置名称。"""
        data = self.coordinator.data.get("data", {})
        loc_name = data.get("location", {}).get("address")
        _LOGGER.debug("设备追踪器位置名称: %s, 原始数据: %s", loc_name, data)
        return loc_name

    @property
    def battery_level(self) -> int | None:
        """返回设备的电池电量。"""
        data = self.coordinator.data.get("data", {})
        battery = data.get("info", {}).get("battery")
        _LOGGER.debug("设备追踪器电池电量: %s, 原始数据: %s", battery, data)
        return battery