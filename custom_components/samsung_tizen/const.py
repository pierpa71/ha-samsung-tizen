"""Constants for the Samsung TV (Tizen) integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "samsung_tizen"

CONF_BROADCAST: Final = "broadcast_address"
DEFAULT_BROADCAST: Final = "255.255.255.255"

# Name shown on the TV in the "allow this device" popup.
CLIENT_NAME: Final = "Home Assistant"

REST_PORT: Final = 8001
WS_PORT_TOKEN: Final = 8002  # wss, used by TVs that support token auth (2018+)
WS_PORT_LEGACY: Final = 8001  # ws, 2016/2017 models without token auth

TIMEOUT: Final = 5
PAIRING_TIMEOUT: Final = 45
SCAN_INTERVAL: Final = timedelta(seconds=10)

# After a power command, report the requested state for this long, because
# the TV keeps answering (or stays silent) for a while during transitions.
POWER_GRACE_SECONDS: Final = 25

# Source name -> remote key.
SOURCES: Final[dict[str, str]] = {
    "TV": "KEY_TV",
    "HDMI": "KEY_HDMI",
    "HDMI 1": "KEY_HDMI1",
    "HDMI 2": "KEY_HDMI2",
    "HDMI 3": "KEY_HDMI3",
    "HDMI 4": "KEY_HDMI4",
}

# App name -> Tizen app id. Also launchable with media_player.play_media
# (media_content_type: app, media_content_id: <app id>).
APPS: Final[dict[str, str]] = {
    "Netflix": "3201907018807",
    "YouTube": "111299001912",
    "Prime Video": "3201910019365",
    "Disney+": "3201901017640",
    "Apple TV": "3201807016597",
    "Spotify": "3201606009684",
    "Plex": "3201512006963",
}
