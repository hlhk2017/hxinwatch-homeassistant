# hxinwatch/config_flow.py
"""HXinWatch集成的配置流程。"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
# 移除了 homeassistant.helpers.selector 的导入，因为它不再需要

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# 定义配置表单的schema
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("token"): str,
        vol.Required("imei"): str,
        vol.Optional("language", default="zh-Hans"): str,
        # 新增：刷新时间设置，使用数字输入框和范围验证
        vol.Optional(
            "scan_interval",
            default=30, # UI 中的默认值
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)), # 直接验证整数范围
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """验证用户输入的数据。"""
    # 在这里验证用户输入，例如尝试使用提供的token和imei连接到API
    # 如果验证失败，抛出相应的异常
    
    # 示例实现，实际中应替换为真实的API调用
    if len(data["token"]) < 32:
        raise InvalidAuth
    
    # 如果验证成功，返回包含设备信息的字典
    return {"title": "HXinWatch Device"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理HXinWatch集成的配置流程。"""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理用户发起的配置流程。"""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception: # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(user_input["imei"])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """无法连接到API的错误。"""


class InvalidAuth(HomeAssistantError):
    """认证失败的错误。"""