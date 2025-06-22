# hxinwatch/sensor.py
"""支持HXinWatch设备的传感器平台。"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN, 
    SENSOR_TYPE_BATTERY, 
    SENSOR_TYPE_HEART_RATE, 
    SENSOR_TYPE_OXYGEN, 
    SENSOR_TYPE_STEPS, 
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_TYPE_CONTACT_COUNT,
    SENSOR_TYPE_ALARM_COUNT,
)

_LOGGER = logging.getLogger(__name__)

# 定义传感器类型和描述
SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_TYPE_BATTERY,
        name="电池电量",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_HEART_RATE,
        name="心率",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="BPM",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_OXYGEN,
        name="血氧饱和度",
        icon="mdi:water",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_TEMPERATURE,
        name="体温",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_STEPS,
        name="步数",
        icon="mdi:walk",
        native_unit_of_measurement="steps",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_CONTACT_COUNT,
        name="通讯录数量",
        icon="mdi:card-account-details-outline",
        native_unit_of_measurement="contacts",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_TYPE_ALARM_COUNT,
        name="闹钟数量",
        icon="mdi:alarm",
        native_unit_of_measurement="alarms",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置配置入口的传感器实体。"""
    integration_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = integration_data["coordinator"]
    
    entities = []
    _LOGGER.debug("开始设置传感器实体，协调器数据: %s", coordinator.data)
    for description in SENSOR_TYPES:
        entities.append(HXinWatchSensor(coordinator, description, entry.unique_id))
    
    async_add_entities(entities)


class HXinWatchSensor(CoordinatorEntity, SensorEntity):
    """表示HXinWatch传感器的实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: SensorEntityDescription,
        device_id: str | None,
    ) -> None:
        """初始化HXinWatch传感器。"""
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
    def native_value(self) -> StateType:
        """返回传感器的值。"""
        data = self.coordinator.data.get("data", {})
        _LOGGER.debug("传感器 '%s' 获取到协调器数据（已解析顶层 'data'）：%s", self.entity_description.key, data)
        
        if self.entity_description.key == SENSOR_TYPE_BATTERY:
            value = data.get("info", {}).get("battery")
            _LOGGER.debug("传感器 '%s' 电池值: %s", self.entity_description.key, value)
            return value
        
        if self.entity_description.key == SENSOR_TYPE_HEART_RATE:
            value = data.get("heart", {}).get("heart")
            _LOGGER.debug("传感器 '%s' 心率值: %s", self.entity_description.key, value)
            return value
        
        if self.entity_description.key == SENSOR_TYPE_OXYGEN:
            value = data.get("oxygen", {}).get("oxygen")
            _LOGGER.debug("传感器 '%s' 氧饱和度值: %s", self.entity_description.key, value)
            return value
        
        if self.entity_description.key == SENSOR_TYPE_TEMPERATURE:
            value = data.get("temperature", {}).get("temperature")
            _LOGGER.debug("传感器 '%s' 温度值: %s", self.entity_description.key, value)
            return value
        
        if self.entity_description.key == SENSOR_TYPE_STEPS:
            value = data.get("sport", {}).get("step")
            _LOGGER.debug("传感器 '%s' 步数值: %s", self.entity_description.key, value)
            return value

        if self.entity_description.key == SENSOR_TYPE_CONTACT_COUNT:
            contacts = data.get("contacts", [])
            _LOGGER.debug("传感器 '%s' 通讯录列表: %s, 数量: %s", self.entity_description.key, contacts, len(contacts))
            return len(contacts)

        if self.entity_description.key == SENSOR_TYPE_ALARM_COUNT:
            alarms = data.get("alarms", [])
            _LOGGER.debug("传感器 '%s' 闹钟列表: %s, 数量: %s", self.entity_description.key, alarms, len(alarms))
            return len(alarms)
        
        _LOGGER.debug("传感器 '%s' 未找到对应数据", self.entity_description.key)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """返回传感器的额外状态属性。"""
        data = self.coordinator.data.get("data", {})
        
        if self.entity_description.key == SENSOR_TYPE_CONTACT_COUNT:
            contacts = data.get("contacts", [])
            return {"contacts": contacts}

        if self.entity_description.key == SENSOR_TYPE_ALARM_COUNT:
            alarms = data.get("alarms", [])
            return {"alarms": alarms}
            
        return None