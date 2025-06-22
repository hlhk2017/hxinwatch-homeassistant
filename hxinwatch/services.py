# hxinwatch/services.py
"""HXinWatch集成的服务实现。"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol # 导入 voluptuous

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv # 导入 config_validation 模块
from homeassistant.helpers import entity_registry as er # 导入 entity_registry 模块
from homeassistant.helpers import device_registry as dr # 导入 device_registry 模块


from .const import (
    DOMAIN,
    SERVICE_ADD_CONTACT,
    SERVICE_DELETE_CONTACT,
    SERVICE_ADD_ALARM,
    SERVICE_DELETE_ALARM,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """设置HXinWatch集成的服务。"""

    async def get_api_instance(call: ServiceCall):
        """辅助函数：安全地从 hass.data 中获取 API 实例，通过 entity_id 或 entry_id 推断。"""
        entry_id = None

        # 优先从 call.data 中直接获取 entry_id
        if "entry_id" in call.data and call.data["entry_id"]:
            entry_id = call.data["entry_id"]
            _LOGGER.debug("从服务调用数据中获取到 entry_id: %s", entry_id)
        elif "entity_id" in call.data and call.data["entity_id"]:
            # 如果没有 entry_id，尝试从 entity_id 推断
            entity_id_target = call.data["entity_id"]
            _LOGGER.debug("从服务调用数据中获取到 entity_id: %s, 尝试推断 entry_id", entity_id_target)

            # 获取实体注册表
            ent_reg = er.async_get(hass)
            entity_entry = ent_reg.async_get(entity_id_target)

            if entity_entry and entity_entry.config_entry_id:
                entry_id = entity_entry.config_entry_id
                _LOGGER.debug("通过实体注册表推断到 entry_id: %s", entry_id)
            elif entity_entry and entity_entry.device_id:
                # 如果实体关联到设备，尝试通过设备注册表获取 config_entry_id
                dev_reg = dr.async_get(hass)
                device_entry = dev_reg.async_get(entity_entry.device_id)
                if device_entry and device_entry.config_entries:
                    # 通常一个设备只有一个配置入口，取第一个
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
            week = call.data.get("week", "0000000")
            status = call.data.get("status", 1)

            alarms = await api.async_get_alarms()

            new_alarm = {
                "name": name,
                "time": time,
                "week": week,
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
    # 统一的服务基础 schema，接受 entity_id 或 entry_id
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
            vol.Required("contact_id"): cv.positive_int, # 假设 contact_id 是正整数
        })
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_ALARM,
        add_alarm,
        schema=BASE_SERVICE_SCHEMA.extend({
            vol.Required("name"): str,
            vol.Required("time"): str, # HH:MM 格式，这里不严格验证
            vol.Optional("week", default="0000000"): str, # 7位二进制字符串
            vol.Optional("status", default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)), # 0或1
        })
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_ALARM,
        delete_alarm,
        schema=BASE_SERVICE_SCHEMA.extend({
            vol.Required("alarm_id"): str, # 假设 alarm_id 是字符串
        })
    )