# hxinwatch/sensor.py
from __future__ import annotations # <--- 确保这一行是文件的绝对第一行！

import logging
from typing import Any, List

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

# 星期映射辅助函数 (放在所有常规导入之后，在其他代码之前)
# Home Assistant 星期缩写到 API 7位二进制字符串索引的映射 (周一为0，周日为6)
HA_TO_API_WEEKDAYS_MAP = {
    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
}
# API 7位二进制字符串索引到中文星期名称的映射 (周一为0，周日为6)
API_WEEKDAYS_ZH = [
    "周一", "周二", "周三", "周四", "周五", "周六", "周日"
]

def _convert_weekdays_to_binary(weekdays: List[str]) -> str:
    """将 Home Assistant 的星期列表（如 ['mon', 'wed']）转换为 7 位二进制字符串（Mon-Sun 顺序）。"""
    binary = ['0'] * 7
    for day in weekdays:
        if day in HA_TO_API_WEEKDAYS_MAP:
            binary[HA_TO_API_WEEKDAYS_MAP[day]] = '1'
    return "".join(binary)

def _convert_binary_to_weekdays_string(binary_week: str) -> str:
    """将 7 位二进制星期字符串（Mon-Sun 顺序，如 '0110001'）转换为人类可读的星期字符串。"""
    if not isinstance(binary_week, str) or len(binary_week) != 7:
        return "未知"
    
    selected_days = []
    for i, bit in enumerate(binary_week):
        if bit == '1':
            selected_days.append(API_WEEKDAYS_ZH[i])
    
    if not selected_days:
        return "不重复"
    if len(selected_days) == 7:
        return "每天"
    if selected_days == ["周一", "周二", "周三", "周四", "周五"]:
        return "工作日"
    if selected_days == ["周六", "周日"]:
        return "周末"
    
    return ", ".join(selected_days)


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
        icon="mdi:water-percent",
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
            "name": "华芯沃设备",
            "manufacturer": "华芯沃",
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
            alarms_raw = data.get("alarms", [])
            # 复制并转换闹钟列表中的 week 字段
            alarms_display = []
            for alarm in alarms_raw:
                alarm_copy = alarm.copy() # 复制字典以避免修改原始协调器数据
                if "week" in alarm_copy:
                    alarm_copy["week_readable"] = _convert_binary_to_weekdays_string(alarm_copy["week"])
                alarms_display.append(alarm_copy)
            return {"alarms": alarms_display}
            
        return None
