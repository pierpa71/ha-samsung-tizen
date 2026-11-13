"""Polling coordinator and shared power/command logic."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .bridge import AuthDenied, CannotConnect, SamsungTVBridge
from .const import (
    APP_LIST_MAX_ATTEMPTS,
    APPS,
    HIDDEN_APP_IDS,
    CONF_BROADCAST,
    DEFAULT_BROADCAST,
    DOMAIN,
    POWER_GRACE_SECONDS,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type SamsungTizenConfigEntry = ConfigEntry[SamsungTVCoordinator]


@dataclass
class TVState:
    """What the last poll found."""

    power: str  # "on", "standby" or "off"
    info: dict[str, Any] | None


class SamsungTVCoordinator(DataUpdateCoordinator[TVState]):
    """Polls the TV's REST API and runs commands for all entities."""

    config_entry: SamsungTizenConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SamsungTizenConfigEntry,
        bridge: SamsungTVBridge,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.title}",
            update_interval=SCAN_INTERVAL,
        )
        self.bridge = bridge
        self._expected_on: bool | None = None
        self._expected_until = 0.0
        # name -> (app id, launch type); replaced by the TV's own list once read.
        self.apps: dict[str, tuple[str, str]] = dict(APPS)
        self._app_list_attempts = 0

    async def _async_update_data(self) -> TVState:
        info = await self.bridge.async_device_info()
        if info is None:
            power = "off"
        else:
            # Models without PowerState only answer REST while on.
            power_state = info.get("device", {}).get("PowerState", "on")
            power = "on" if power_state == "on" else "standby"
        if power != "on":
            await self.bridge.async_close()
        elif self._app_list_attempts < APP_LIST_MAX_ATTEMPTS:
            await self._async_load_apps()
        return TVState(power=power, info=info)

    async def _async_load_apps(self) -> None:
        self._app_list_attempts += 1
        try:
            installed = await self.bridge.async_app_list()
        except (AuthDenied, CannotConnect) as err:
            _LOGGER.debug("Could not read app list: %s", err)
            return
        if not installed:
            _LOGGER.debug("TV did not return an app list, using defaults")
            return
        apps: dict[str, tuple[str, str]] = {}
        for app in installed:
            app_id, name = app.get("appId"), app.get("name")
            if not app_id or not name or app_id in HIDDEN_APP_IDS:
                continue
            # Same convention as Samsung's own apps: type 2 = deep link.
            launch = "DEEP_LINK" if app.get("app_type") == 2 else "NATIVE_LAUNCH"
            apps[name] = (app_id, launch)
        self.apps = dict(sorted(apps.items(), key=lambda kv: kv[0].casefold()))
        self._app_list_attempts = APP_LIST_MAX_ATTEMPTS
        _LOGGER.debug("Loaded %d apps from the TV", len(self.apps))

    # ---- shared state -------------------------------------------------

    @property
    def is_on(self) -> bool:
        """Polled power, overridden briefly after a power command."""
        if self._expected_on is not None and time.monotonic() < self._expected_until:
            return self._expected_on
        return self.data is not None and self.data.power == "on"

    @property
    def mac(self) -> str | None:
        return self.config_entry.options.get(CONF_MAC) or self.config_entry.data.get(
            CONF_MAC
        )

    @property
    def can_turn_on(self) -> bool:
        return bool(self.mac) or (self.data is not None and self.data.power == "standby")

    @property
    def device_info(self) -> DeviceInfo:
        entry = self.config_entry
        connections = {(CONNECTION_NETWORK_MAC, self.mac)} if self.mac else set()
        return DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            connections=connections,
            manufacturer="Samsung",
            model=entry.data.get("model"),
            name=entry.title,
        )

    def _expect(self, on: bool) -> None:
        self._expected_on = on
        self._expected_until = time.monotonic() + POWER_GRACE_SECONDS
        self.async_update_listeners()

    # ---- commands -----------------------------------------------------

    async def _run(self, coro: Any) -> None:
        try:
            await coro
        except AuthDenied as err:
            self.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError(
                "Il TV ha rifiutato la connessione: ripeti l'abbinamento"
            ) from err
        except CannotConnect as err:
            raise HomeAssistantError(f"TV non raggiungibile: {err}") from err

    async def async_send_keys(self, keys: list[str], delay: float = 0.3) -> None:
        if not self.is_on:
            raise HomeAssistantError("Il TV è spento")
        await self._run(self.bridge.async_send_keys(keys, delay))

    async def async_launch_app(self, app: str) -> None:
        """Launch an app by name (from the app list) or by Tizen app id."""
        if not self.is_on:
            raise HomeAssistantError("Il TV è spento")
        app_id, launch = self.apps.get(app) or next(
            (v for v in self.apps.values() if v[0] == app), (app, "DEEP_LINK")
        )
        await self._run(self.bridge.async_launch_app(app_id, launch))

    async def async_set_channel(self, channel: str) -> None:
        channel = channel.strip()
        if not channel.isdigit():
            raise HomeAssistantError("Il canale deve essere un numero")
        await self.async_send_keys([f"KEY_{d}" for d in channel] + ["KEY_ENTER"], 0.2)

    async def async_turn_on(self) -> None:
        if self.data is not None and self.data.power == "standby":
            await self._run(self.bridge.async_send_keys(["KEY_POWER"]))
        elif self.mac:
            broadcast = self.config_entry.options.get(CONF_BROADCAST, DEFAULT_BROADCAST)
            await self.bridge.async_wake(self.mac, broadcast)
        else:
            raise HomeAssistantError(
                "Per accendere il TV serve il MAC address (Wake-on-LAN): "
                "impostalo nelle opzioni dell'integrazione"
            )
        self._expect(True)

    async def async_turn_off(self) -> None:
        await self._run(self.bridge.async_send_keys(["KEY_POWER"]))
        self._expect(False)
        await self.bridge.async_close()
