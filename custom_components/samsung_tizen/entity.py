"""Base entity shared by all platforms."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SamsungTVCoordinator


class SamsungTVEntity(CoordinatorEntity[SamsungTVCoordinator]):
    """An entity of the TV device, available only while the TV is on."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SamsungTVCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{key}"
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        return self.coordinator.is_on
