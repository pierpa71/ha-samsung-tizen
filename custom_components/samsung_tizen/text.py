"""Type a channel number to switch to it."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SamsungTizenConfigEntry, SamsungTVCoordinator
from .entity import SamsungTVEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SamsungTizenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([SamsungTVChannelText(entry.runtime_data)])


class SamsungTVChannelText(SamsungTVEntity, TextEntity):
    """Channel number; setting it sends the digits followed by OK."""

    _attr_translation_key = "channel"
    _attr_icon = "mdi:numeric"
    _attr_mode = TextMode.TEXT
    _attr_native_min = 1
    _attr_native_max = 4
    _attr_pattern = r"^\d{1,4}$"
    _attr_native_value = None

    def __init__(self, coordinator: SamsungTVCoordinator) -> None:
        super().__init__(coordinator, "channel")

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_set_channel(value)
        self._attr_native_value = value
        self.async_write_ha_state()
