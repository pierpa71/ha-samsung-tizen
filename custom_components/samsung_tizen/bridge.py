"""Connection to a Samsung Tizen TV (REST for status, WebSocket for commands)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
import logging
from typing import Any

import aiohttp
from samsungtvws.async_remote import SamsungTVWSAsyncRemote
from samsungtvws.async_rest import SamsungTVAsyncRest
from samsungtvws.exceptions import (
    ConnectionFailure,
    HttpApiError,
    ResponseError,
    UnauthorizedError,
)
from samsungtvws.remote import ChannelEmitCommand, SendRemoteKey
from websockets.exceptions import WebSocketException
import wakeonlan

from .const import CLIENT_NAME, PAIRING_TIMEOUT, REST_PORT, TIMEOUT

_LOGGER = logging.getLogger(__name__)

_WS_ERRORS = (ConnectionFailure, WebSocketException, OSError, TimeoutError)


class CannotConnect(Exception):
    """The TV is not reachable."""


class AuthDenied(Exception):
    """The TV refused the connection (popup denied or token revoked)."""


async def async_get_device_info(
    session: aiohttp.ClientSession, host: str
) -> dict[str, Any]:
    """Read the TV's REST device info, raising CannotConnect if unreachable."""
    rest = SamsungTVAsyncRest(host, session=session, port=REST_PORT, timeout=TIMEOUT)
    try:
        return await rest.rest_device_info()
    except (HttpApiError, ResponseError, aiohttp.ClientError, OSError, TimeoutError) as err:
        raise CannotConnect(str(err)) from err


async def async_pair(host: str, port: int) -> str | None:
    """Open a first connection so the TV shows the allow popup; return the token."""
    remote = SamsungTVWSAsyncRemote(
        host, port=port, timeout=TIMEOUT, key_press_delay=0, name=CLIENT_NAME
    )
    try:
        async with asyncio.timeout(PAIRING_TIMEOUT):
            await remote.open()
    except UnauthorizedError as err:
        raise AuthDenied from err
    except _WS_ERRORS as err:
        raise CannotConnect(str(err)) from err
    finally:
        with contextlib.suppress(*_WS_ERRORS):
            await remote.close()
    return remote.token


class SamsungTVBridge:
    """Keeps one WebSocket connection to the TV and reconnects when needed."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        token: str | None,
        on_new_token: Callable[[str], None] | None = None,
    ) -> None:
        self.session = session
        self.host = host
        self.port = port
        self.token = token
        self._on_new_token = on_new_token
        self._remote: SamsungTVWSAsyncRemote | None = None
        self._lock = asyncio.Lock()

    async def async_device_info(self) -> dict[str, Any] | None:
        """Return REST device info, or None when the TV is unreachable."""
        try:
            return await async_get_device_info(self.session, self.host)
        except CannotConnect:
            return None

    async def _async_get_remote(self) -> SamsungTVWSAsyncRemote:
        if self._remote is not None and self._remote.is_alive():
            return self._remote
        await self._async_close_remote()

        remote = SamsungTVWSAsyncRemote(
            self.host,
            token=self.token,
            port=self.port,
            timeout=TIMEOUT,
            key_press_delay=0,
            name=CLIENT_NAME,
        )
        try:
            async with asyncio.timeout(TIMEOUT * 2):
                await remote.start_listening()
        except BaseException:
            with contextlib.suppress(*_WS_ERRORS):
                await remote.close()
            raise

        if remote.token and remote.token != self.token:
            _LOGGER.debug("TV %s issued a new token", self.host)
            self.token = remote.token
            if self._on_new_token:
                self._on_new_token(remote.token)

        self._remote = remote
        return remote

    async def _async_close_remote(self) -> None:
        remote, self._remote = self._remote, None
        if remote is not None:
            with contextlib.suppress(*_WS_ERRORS):
                await remote.close()

    async def _async_send(self, commands: list[Any], delay: float) -> None:
        async with self._lock:
            for attempt in range(2):
                try:
                    remote = await self._async_get_remote()
                    await remote.send_commands(commands, key_press_delay=delay)
                except UnauthorizedError as err:
                    await self._async_close_remote()
                    raise AuthDenied from err
                except _WS_ERRORS as err:
                    # Stale connection (TV slept, network blip): retry once.
                    await self._async_close_remote()
                    if attempt:
                        raise CannotConnect(str(err) or type(err).__name__) from err
                else:
                    return

    async def async_send_keys(self, keys: list[str], delay: float = 0.3) -> None:
        """Send remote keys (e.g. KEY_VOLUP) in order."""
        await self._async_send([SendRemoteKey.click(key) for key in keys], delay)

    async def async_launch_app(self, app_id: str, app_type: str = "DEEP_LINK") -> None:
        """Launch an app by its Tizen id."""
        await self._async_send([ChannelEmitCommand.launch_app(app_id, app_type)], 0)

    async def async_app_list(self) -> list[dict[str, Any]] | None:
        """Return the TV's installed apps (None if the model doesn't support it)."""
        async with self._lock:
            try:
                remote = await self._async_get_remote()
                return await remote.app_list()
            except UnauthorizedError as err:
                await self._async_close_remote()
                raise AuthDenied from err
            except _WS_ERRORS as err:
                await self._async_close_remote()
                raise CannotConnect(str(err) or type(err).__name__) from err

    async def async_wake(self, mac: str, broadcast: str) -> None:
        """Send a Wake-on-LAN magic packet."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: wakeonlan.send_magic_packet(mac, ip_address=broadcast),
        )

    async def async_close(self) -> None:
        """Close the WebSocket connection."""
        async with self._lock:
            await self._async_close_remote()
