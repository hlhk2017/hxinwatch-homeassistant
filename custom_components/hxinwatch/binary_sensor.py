# hxinwatch/binary_sensor.py
"""支持HXinWatch设备的二进制传感器平台。"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, BINARY_SENSOR_TYPE_LOW_BATTERY

_LOGGER = logging.getLogger(__name__)

# 定义二进制传感器类型和描述
BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_TYPE_LOW_BATTERY,
        name="低电量",
        icon="mdi:battery-alert",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置配置入口的二进制传感器实体。"""
    integration_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = integration_data["coordinator"]
    
    entities = []
    _LOGGER.debug("开始设置二进制传感器实体，协调器数据: %s", coordinator.data)
    for description in BINARY_SENSOR_TYPES:
        entities.append(HXinWatchBinarySensor(coordinator, description, entry.unique_id))
    
    async_add_entities(entities)


class HXinWatchBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """表示HXinWatch二进制传感器的实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: BinarySensorEntityDescription,
        device_id: str | None,
    ) -> None:
        """初始化HXinWatch二进制传感器。"""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": "华芯沃设备", # 修改这里
            "manufacturer": "华芯沃", # 修改这里
            "model": "Smart Watch",
        }

    @property
    def is_on(self) -> bool:
        """返回二进制传感器的状态。"""
        data = self.coordinator.data.get("data", {})
        battery_level = data.get("info", {}).get("battery")
        _LOGGER.debug("二进制传感器 '%s' 获取到协调器数据（已解析顶层 'data'）：%s, 电池电量: %s", self.entity_description.key, data, battery_level)
        
        return battery_level is not None and battery_level < 15