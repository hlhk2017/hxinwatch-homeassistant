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
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .api import HXinWatchAPI

_LOGGER = logging.getLogger(__name__)

# 定义配置表单的schema
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("imei"): str,  # IMEI 是必填项
        vol.Required("appid"): str, # AppID 是必填项，用于获取Token
        vol.Optional("language", default="zh-Hans"): str,
        vol.Optional(
            "scan_interval",
            default=30,
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """验证用户输入的数据。"""
    imei = data["imei"]
    appid = data["appid"]
    language = data.get("language", "zh-Hans")

    session = async_get_clientsession(hass)
    # HXinWatchAPI 现在需要 appid 作为初始化参数
    api = HXinWatchAPI(
        imei=imei,
        appid=appid,
        language=language,
        session=session,
    )

    try:
        # 首先尝试通过 AppID 获取 Token (此步骤不再需要IMEI)
        await api.async_get_token_by_appid()
        _LOGGER.debug("通过 AppID 获取 Token 成功。")
        
        # 然后尝试使用获取到的 Token 和用户提供的 IMEI 获取设备状态进行验证
        await api.async_get_device_status()
        _LOGGER.debug("使用新获取的Token和IMEI获取设备状态成功，输入验证通过。")

    except Exception as e:
        _LOGGER.warning("HXinWatch输入验证失败: %s", e)
        if isinstance(e, HomeAssistantError):
            raise e
        # 尝试区分认证错误和连接错误
        if "401" in str(e) or "Unauthorized" in str(e) or "认证失败" in str(e) or "获取Token失败" in str(e):
             raise InvalidAuth("认证信息（AppID或IMEI）无效。") from e
        raise CannotConnect(f"无法连接或获取设备数据: {e}") from e
    
    return {"title": f"HXinWatch Device ({imei})"}


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
