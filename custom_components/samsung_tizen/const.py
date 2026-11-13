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

# How many polls (while on) may try to read the installed-app list.
APP_LIST_MAX_ATTEMPTS: Final = 3

# Source name -> remote key.
SOURCES: Final[dict[str, str]] = {
    "TV": "KEY_TV",
    "HDMI": "KEY_HDMI",
    "HDMI 1": "KEY_HDMI1",
    "HDMI 2": "KEY_HDMI2",
    "HDMI 3": "KEY_HDMI3",
    "HDMI 4": "KEY_HDMI4",
}

# Fallback apps (name -> (Tizen app id, launch type)) used until the TV
# returns its own installed-app list. IDs vary by model year.
APPS: Final[dict[str, tuple[str, str]]] = {
    "Netflix": ("11101200001", "DEEP_LINK"),
    "YouTube": ("111299001912", "DEEP_LINK"),
    "Prime Video": ("3201512006785", "DEEP_LINK"),
    "Disney+": ("3201901017640", "DEEP_LINK"),
    "RaiPlay": ("111399002034", "DEEP_LINK"),
    "Mediaset Infinity": ("3201609010702", "DEEP_LINK"),
    "DAZN": ("3201806016390", "DEEP_LINK"),
    "NOW": ("3201803015896", "DEEP_LINK"),
    "Apple TV": ("3201807016597", "NATIVE_LAUNCH"),
    "Spotify": ("3201606009684", "DEEP_LINK"),
    "Internet": ("org.tizen.browser", "NATIVE_LAUNCH"),
}

# Installed apps that are not worth showing in the app picker.
HIDDEN_APP_IDS: Final = {"3201909019271", "20182100010"}  # privacy choices, e-Manual

# Remote buttons: key -> (remote key, icon).
BUTTONS: Final[dict[str, tuple[str, str]]] = {
    "up": ("KEY_UP", "mdi:chevron-up"),
    "down": ("KEY_DOWN", "mdi:chevron-down"),
    "left": ("KEY_LEFT", "mdi:chevron-left"),
    "right": ("KEY_RIGHT", "mdi:chevron-right"),
    "enter": ("KEY_ENTER", "mdi:checkbox-blank-circle-outline"),
    "back": ("KEY_RETURN", "mdi:arrow-u-left-top"),
    "exit": ("KEY_EXIT", "mdi:exit-to-app"),
    "home": ("KEY_HOME", "mdi:home"),
    "menu": ("KEY_MENU", "mdi:cog"),
    "info": ("KEY_INFO", "mdi:information-outline"),
    "guide": ("KEY_GUIDE", "mdi:television-guide"),
    "channel_list": ("KEY_CH_LIST", "mdi:format-list-numbered"),
    "source": ("KEY_SOURCE", "mdi:import"),
    "channel_up": ("KEY_CHUP", "mdi:arrow-up-bold"),
    "channel_down": ("KEY_CHDOWN", "mdi:arrow-down-bold"),
    "volume_up": ("KEY_VOLUP", "mdi:volume-plus"),
    "volume_down": ("KEY_VOLDOWN", "mdi:volume-minus"),
    "mute": ("KEY_MUTE", "mdi:volume-off"),
    "play": ("KEY_PLAY", "mdi:play"),
    "pause": ("KEY_PAUSE", "mdi:pause"),
    "rewind": ("KEY_REWIND", "mdi:rewind"),
    "fast_forward": ("KEY_FF", "mdi:fast-forward"),
    "red": ("KEY_RED", "mdi:circle"),
    "green": ("KEY_GREEN", "mdi:circle"),
    "yellow": ("KEY_YELLOW", "mdi:circle"),
    "blue": ("KEY_BLUE", "mdi:circle"),
}
