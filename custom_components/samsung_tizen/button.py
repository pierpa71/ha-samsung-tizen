"""Buttons for navigation, channels, volume and playback."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import BUTTONS
from .coordinator import SamsungTizenConfigEntry, SamsungTVCoordinator
from .entity import SamsungTVEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SamsungTizenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        SamsungTVButton(coordinator, key, remote_key, icon)
        for key, (remote_key, icon) in BUTTONS.items()
    )


class SamsungTVButton(SamsungTVEntity, ButtonEntity):
    """Press one key of the remote."""

    def __init__(
        self, coordinator: SamsungTVCoordinator, key: str, remote_key: str, icon: str
    ) -> None:
        super().__init__(coordinator, f"btn_{key}")
        self._attr_translation_key = key
        self._attr_icon = icon
        self._remote_key = remote_key

    async def async_press(self) -> None:
        await self.coordinator.async_send_keys([self._remote_key])
