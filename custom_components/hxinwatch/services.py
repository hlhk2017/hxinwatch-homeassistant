# hxinwatch/services.py
from __future__ import annotations # <--- 确保这一行是文件的绝对第一行！

import logging
from typing import Any, List, Union # 导入 Union
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    SERVICE_ADD_CONTACT,
    SERVICE_DELETE_CONTACT,
    SERVICE_ADD_ALARM,
    SERVICE_DELETE_ALARM,
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
# 中文星期名称到 Home Assistant 星期缩写的映射 (用于输入转换)
CHINESE_TO_HA_WEEKDAYS_MAP = {
    "周一": 'mon', "周二": 'tue', "周三": 'wed', "周四": 'thu', "周五": 'fri',
    "周六": 'sat', "周日": 'sun'
}
# 数字到 Home Assistant 星期缩写的映射 (用于输入转换, 1=周一, 7=周日)
NUM_TO_HA_WEEKDAYS_MAP = {
    1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat', 7: 'sun'
}


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

def _normalize_weekday_input(item: Union[str, int]) -> str:
    """
    将星期输入（数字、中文星期字符串或 HA 缩写字符串）标准化为 HA 星期缩写字符串。
    如果输入无效，则抛出 voluptuous.Invalid。
    """
    if isinstance(item, int):
        if item not in NUM_TO_HA_WEEKDAYS_MAP:
            raise vol.Invalid(f"数字 '{item}' 不是有效的星期数字 (1-7)。")
        return NUM_TO_HA_WEEKDAYS_MAP[item]
    
    if isinstance(item, str):
        item_lower = item.lower()
        if item_lower in HA_TO_API_WEEKDAYS_MAP: # 已经是有效的 HA 缩写
            return item_lower
        if item in CHINESE_TO_HA_WEEKDAYS_MAP: # 是中文星期名称
            return CHINESE_TO_HA_WEEKDAYS_MAP[item]
        raise vol.Invalid(f"字符串 '{item}' 不是有效的星期名称或缩写。")
    
    raise vol.Invalid(f"星期输入 '{item}' 类型无效，必须是数字或字符串。")


async def async_setup_services(hass: HomeAssistant) -> None:
    """设置HXinWatch集成的服务。"""

    async def get_api_instance(call: ServiceCall):
        """辅助函数：安全地从 hass.data 中获取 API 实例，通过 entity_id 或 entry_id 推断。"""
        entry_id = None
        
        if "entry_id" in call.data and call.data["entry_id"]:
            entry_id = call.data["entry_id"]
            _LOGGER.debug("从服务调用数据中获取到 entry_id: %s", entry_id)
        elif "entity_id" in call.data and call.data["entity_id"]:
            entity_id_target = call.data["entity_id"]
            _LOGGER.debug("从服务调用数据中获取到 entity_id: %s, 尝试推断 entry_id", entity_id_target)

            ent_reg = er.async_get(hass)
            entity_entry = ent_reg.async_get(entity_id_target)

            if entity_entry and entity_entry.config_entry_id:
                entry_id = entity_entry.config_entry_id
                _LOGGER.debug("通过实体注册表推断到 entry_id: %s", entry_id)
            elif entity_entry and entity_entry.device_id:
                dev_reg = dr.async_get(hass)
                device_entry = dev_reg.async_get(entity_entry.device_id)
                if device_entry and device_entry.config_entries:
                    entry_id = next(iter(device_entry.config_entries), None)
                    _LOGGER.debug("通过设备注册表推断到 entry_id: %s", entry_id)
        
        if not entry_id:
            _LOGGER.error("服务调用缺少有效的 'entry_id' 或无法从 'entity_id' 推断。调用数据: %s", call.data)
            raise HomeAssistantError("服务调用必须提供有效的 'entry_id' 或关联的 'entity_id'。")
        
        integration_data = hass.data[DOMAIN].get(entry_id)
        if not integration_data:
            _LOGGER.error("未找到配置入口 ID 为 '%s' 的集成数据。请确保集成已正确设置并加载。", entry_id)
            raise HomeAssistantError(f"未找到集成数据，请确保集成已设置并加载: {entry_id}")
            
        api = integration_data.get("api")
        if not api:
            _LOGGER.error("未找到配置入口 ID 为 '%s' 的 API 实例。集成数据: %s", entry_id, integration_data)
            raise HomeAssistantError(f"API 实例不可用: {entry_id}")
        return api


    async def add_contact(call: ServiceCall) -> None:
        """添加联系人服务。"""
        try:
            api = await get_api_instance(call)
            name = call.data["name"]
            phone = call.data["phone"]
            
            contacts = await api.async_get_contacts()
            
            for contact in contacts:
                if contact["phone"] == phone:
                    raise HomeAssistantError(f"联系人 {phone} 已存在")
            
            new_contact = {
                "name": name,
                "phone": phone,
            }
            
            contacts.append(new_contact)
            await api.async_update_contacts(contacts)
            
            _LOGGER.info("已添加新联系人: %s", name)
        except HomeAssistantError as e:
            _LOGGER.error("添加联系人失败: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("添加联系人时发生意外错误: %s", e)
            raise HomeAssistantError(f"添加联系人时发生意外错误: {e}")


    async def delete_contact(call: ServiceCall) -> None:
        """删除联系人服务。"""
        try:
            api = await get_api_instance(call)
            contact_id = call.data["contact_id"]
            
            contacts = await api.async_get_contacts()
            
            contact_to_delete = next((c for c in contacts if c["id"] == contact_id), None)
            if not contact_to_delete:
                raise HomeAssistantError(f"联系人ID {contact_id} 不存在")
            
            contacts = [c for c in contacts if c["id"] != contact_id]
            await api.async_update_contacts(contacts)
            
            _LOGGER.info("已删除联系人ID: %s", contact_id)
        except HomeAssistantError as e:
            _LOGGER.error("删除联系人失败: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("删除联系人时发生意外错误: %s", e)
            raise HomeAssistantError(f"删除联系人时发生意外错误: {e}")


    async def add_alarm(call: ServiceCall) -> None:
        """添加闹钟服务。"""
        try:
            api = await get_api_instance(call)
            name = call.data["name"]
            time = call.data["time"]
            
            # 获取并标准化 week 参数
            # vol.All 已经确保了 week_input_list 是一个列表，且其中每个项通过 _normalize_weekday_input 处理过
            week_input_list = call.data.get("week", []) 
            week_binary = _convert_weekdays_to_binary(week_input_list) # 使用标准化后的列表
            
            status = call.data.get("status", 1)
            
            alarms = await api.async_get_alarms()
            
            new_alarm = {
                "name": name,
                "time": time,
                "week": week_binary, 
                "status": status,
            }
            
            alarms.append(new_alarm)
            await api.async_update_alarms(alarms)
            
            _LOGGER.info("已添加新闹钟: %s at %s", name, time)
        except HomeAssistantError as e:
            _LOGGER.error("添加闹钟失败: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("添加闹钟时发生意外错误: %s", e)
            raise HomeAssistantError(f"添加闹钟时发生意外错误: {e}")


    async def delete_alarm(call: ServiceCall) -> None:
        """删除闹钟服务。"""
        try:
            api = await get_api_instance(call)
            alarm_id = call.data["alarm_id"]
            
            alarms = await api.async_get_alarms()
            
            alarm_to_delete = next((a for a in alarms if a["id"] == alarm_id), None)
            if not alarm_to_delete:
                raise HomeAssistantError(f"闹钟ID {alarm_id} 不存在")
            
            alarms = [a for a in alarms if a["id"] != alarm_id]
            await api.async_update_alarms(alarms)
            
            _LOGGER.info("已删除闹钟ID: %s", alarm_id)
        except HomeAssistantError as e:
            _LOGGER.error("删除闹钟失败: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("删除闹钟时发生意外错误: %s", e)
            raise HomeAssistantError(f"删除闹钟时发生意外错误: {e}")

    # 定义服务 schema
    BASE_SERVICE_SCHEMA = vol.Schema({
        vol.Exclusive("entity_id", "target_identifier"): cv.entity_id,
        vol.Exclusive("entry_id", "target_identifier"): str,
    })

    # 为每个服务注册 schema
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_CONTACT,
        add_contact,
        schema=BASE_SERVICE_SCHEMA.extend({
            vol.Required("name"): str,
            vol.Required("phone"): str,
        })
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_CONTACT,
        delete_contact,
        schema=BASE_SERVICE_SCHEMA.extend({
            vol.Required("contact_id"): cv.positive_int,
        })
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_ALARM,
        add_alarm,
        schema=BASE_SERVICE_SCHEMA.extend({
            vol.Required("name"): str,
            vol.Required("time"): str, # HH:MM 格式，这里不严格验证
            vol.Optional(
                "week",
                default=[], # 默认空列表表示不重复
            ): vol.All(
                cv.ensure_list, # 确保是一个列表
                [_normalize_weekday_input], # 列表中每个项都通过 _normalize_weekday_input 函数处理
            ), 
            vol.Optional("status", default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)), # 0或1
        })
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_ALARM,
        delete_alarm,
        schema=BASE_SERVICE_SCHEMA.extend({
            vol.Required("alarm_id"): str,
        })
    )
