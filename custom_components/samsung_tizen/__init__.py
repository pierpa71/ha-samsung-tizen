"""Samsung TV (Tizen) integration for Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .bridge import SamsungTVBridge
from .const import DOMAIN
from .coordinator import SamsungTizenConfigEntry, SamsungTVCoordinator

PLATFORMS = [
    Platform.BUTTON,
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SELECT,
    Platform.TEXT,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

CARD_FILE = Path(__file__).parent / "frontend" / "samsung-remote-card.js"
CARD_URL = f"/{DOMAIN}/samsung-remote-card.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the remote control card and load it in every dashboard."""
    version = (await async_get_integration(hass, DOMAIN)).version
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_FILE), cache_headers=False)]
    )
    # The version query string makes browsers fetch the card again after updates.
    add_extra_js_url(hass, f"{CARD_URL}?v={version}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SamsungTizenConfigEntry) -> bool:
    """Set up a TV from a config entry."""

    @callback
    def _save_token(token: str) -> None:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_TOKEN: token}
        )

    bridge = SamsungTVBridge(
        async_get_clientsession(hass, verify_ssl=False),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_TOKEN),
        _save_token,
    )
    coordinator = SamsungTVCoordinator(hass, entry, bridge)
    # A TV that is off is a normal state, so the first refresh never fails.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SamsungTizenConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.bridge.async_close()
    return unloaded
