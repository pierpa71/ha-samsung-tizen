"""Remote entity: send any key of the Samsung remote."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    RemoteEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SamsungTizenConfigEntry, SamsungTVCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SamsungTizenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([SamsungTVRemote(entry.runtime_data)])


class SamsungTVRemote(CoordinatorEntity[SamsungTVCoordinator], RemoteEntity):
    """Sends KEY_* codes, e.g. KEY_HOME, KEY_UP, KEY_ENTER, KEY_RETURN."""

    _attr_has_entity_name = True
    _attr_translation_key = "remote"

    def __init__(self, coordinator: SamsungTVCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_remote"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_turn_off()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        repeats = kwargs.get(ATTR_NUM_REPEATS, 1)
        delay = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        keys = [
            key if key.upper().startswith("KEY_") else f"KEY_{key}"
            for key in command
        ]
        keys = [key.upper() for key in keys] * repeats
        await self.coordinator.async_send_keys(keys, delay)
