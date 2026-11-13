"""Config flow: find the TV, then pair (accept the popup on the TV)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac

from .bridge import AuthDenied, CannotConnect, async_get_device_info, async_pair
from .const import (
    CONF_BROADCAST,
    DEFAULT_BROADCAST,
    DOMAIN,
    WS_PORT_LEGACY,
    WS_PORT_TOKEN,
)
from .coordinator import SamsungTizenConfigEntry


class SamsungTizenConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._host = ""
        self._port = WS_PORT_TOKEN
        self._name = ""
        self._mac: str | None = None
        self._model: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(entry: SamsungTizenConfigEntry) -> SamsungTizenOptionsFlow:
        return SamsungTizenOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            try:
                info = await async_get_device_info(
                    async_get_clientsession(self.hass, verify_ssl=False), host
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                device = info.get("device", {})
                await self.async_set_unique_id(device.get("id") or device.get("duid") or host)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})

                self._host = host
                self._name = (
                    user_input.get(CONF_NAME)
                    or device.get("name")
                    or info.get("name")
                    or "Samsung TV"
                )
                self._model = device.get("modelName")
                if mac := device.get("wifiMac"):
                    self._mac = format_mac(mac)
                token_auth = str(device.get("TokenAuthSupport", "false")).lower() == "true"
                self._port = WS_PORT_TOKEN if token_auth else WS_PORT_LEGACY
                return await self.async_step_pair()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): str,
                        vol.Optional(CONF_NAME): str,
                    }
                ),
                user_input,
            ),
            errors=errors,
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                token = await async_pair(self._host, self._port)
            except AuthDenied:
                errors["base"] = "auth_denied"
            except CannotConnect:
                errors["base"] = "pairing_failed"
            else:
                data = {
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_TOKEN: token,
                    CONF_MAC: self._mac,
                    "model": self._model,
                }
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data_updates=data
                    )
                return self.async_create_entry(title=self._name, data=data)

        return self.async_show_form(
            step_id="pair",
            description_placeholders={"name": self._name, "host": self._host},
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        self._host = entry_data[CONF_HOST]
        self._port = entry_data[CONF_PORT]
        self._mac = entry_data.get(CONF_MAC)
        self._model = entry_data.get("model")
        self._name = entry.title
        return await self.async_step_pair()


class SamsungTizenOptionsFlow(OptionsFlowWithReload):
    """MAC address and broadcast for Wake-on-LAN."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            mac = user_input.get(CONF_MAC, "").strip()
            if mac and len(format_mac(mac).split(":")) != 6:
                errors[CONF_MAC] = "invalid_mac"
            else:
                return self.async_create_entry(
                    data={
                        CONF_MAC: format_mac(mac) if mac else "",
                        CONF_BROADCAST: user_input[CONF_BROADCAST].strip(),
                    }
                )

        entry = self.config_entry
        current = {
            CONF_MAC: entry.options.get(CONF_MAC) or entry.data.get(CONF_MAC) or "",
            CONF_BROADCAST: entry.options.get(CONF_BROADCAST, DEFAULT_BROADCAST),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Optional(CONF_MAC): str,
                        vol.Required(CONF_BROADCAST, default=DEFAULT_BROADCAST): str,
                    }
                ),
                user_input or current,
            ),
            errors=errors,
        )
