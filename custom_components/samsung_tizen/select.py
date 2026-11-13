"""Pickers for input source and app."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import SOURCES
from .coordinator import SamsungTizenConfigEntry, SamsungTVCoordinator
from .entity import SamsungTVEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SamsungTizenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([SamsungTVSourceSelect(coordinator), SamsungTVAppSelect(coordinator)])


class SamsungTVSourceSelect(SamsungTVEntity, SelectEntity):
    """Switch input (TV, HDMI...). The TV doesn't report it, so it shows the last choice."""

    _attr_translation_key = "source"
    _attr_icon = "mdi:video-input-hdmi"
    _attr_options = list(SOURCES)
    _attr_current_option = None

    def __init__(self, coordinator: SamsungTVCoordinator) -> None:
        super().__init__(coordinator, "select_source")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_send_keys([SOURCES[option]])
        self._attr_current_option = option
        self.async_write_ha_state()


class SamsungTVAppSelect(SamsungTVEntity, SelectEntity):
    """Open an app installed on the TV."""

    _attr_translation_key = "app"
    _attr_icon = "mdi:apps"
    _attr_current_option = None

    def __init__(self, coordinator: SamsungTVCoordinator) -> None:
        super().__init__(coordinator, "select_app")

    @property
    def options(self) -> list[str]:
        return list(self.coordinator.apps)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_launch_app(option)
        self._attr_current_option = option
        self.async_write_ha_state()
