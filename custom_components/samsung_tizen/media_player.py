"""Media player entity for a Samsung Tizen TV."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import SOURCES
from .coordinator import SamsungTizenConfigEntry, SamsungTVCoordinator

BASE_FEATURES = (
    MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SamsungTizenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([SamsungTVMediaPlayer(entry.runtime_data)])


class SamsungTVMediaPlayer(CoordinatorEntity[SamsungTVCoordinator], MediaPlayerEntity):
    """The TV as a media player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.TV

    def __init__(self, coordinator: SamsungTVCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.unique_id
        self._attr_device_info = coordinator.device_info

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.ON if self.coordinator.is_on else MediaPlayerState.OFF

    @property
    def source_list(self) -> list[str]:
        return [*SOURCES, *self.coordinator.apps]

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        features = BASE_FEATURES
        if self.coordinator.can_turn_on:
            features |= MediaPlayerEntityFeature.TURN_ON
        return features

    async def async_turn_on(self) -> None:
        await self.coordinator.async_turn_on()

    async def async_turn_off(self) -> None:
        await self.coordinator.async_turn_off()

    async def async_volume_up(self) -> None:
        await self.coordinator.async_send_keys(["KEY_VOLUP"])

    async def async_volume_down(self) -> None:
        await self.coordinator.async_send_keys(["KEY_VOLDOWN"])

    async def async_mute_volume(self, mute: bool) -> None:
        # The TV only offers a mute toggle and doesn't report the mute state.
        await self.coordinator.async_send_keys(["KEY_MUTE"])

    async def async_media_play(self) -> None:
        await self.coordinator.async_send_keys(["KEY_PLAY"])

    async def async_media_pause(self) -> None:
        await self.coordinator.async_send_keys(["KEY_PAUSE"])

    async def async_media_stop(self) -> None:
        await self.coordinator.async_send_keys(["KEY_STOP"])

    async def async_media_next_track(self) -> None:
        await self.coordinator.async_send_keys(["KEY_CHUP"])

    async def async_media_previous_track(self) -> None:
        await self.coordinator.async_send_keys(["KEY_CHDOWN"])

    async def async_select_source(self, source: str) -> None:
        if source in SOURCES:
            await self.coordinator.async_send_keys([SOURCES[source]])
        elif source in self.coordinator.apps:
            await self.coordinator.async_launch_app(source)
        else:
            raise HomeAssistantError(f"Sorgente sconosciuta: {source}")

    async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        if media_type == MediaType.APP:
            await self.coordinator.async_launch_app(media_id)
        elif media_type == MediaType.CHANNEL:
            await self.coordinator.async_set_channel(media_id)
        elif media_type == "send_key":
            await self.coordinator.async_send_keys([media_id])
        else:
            raise HomeAssistantError(
                f"Tipo non supportato: {media_type} (usa app, channel o send_key)"
            )
