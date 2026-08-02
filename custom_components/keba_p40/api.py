"""API client for the KEBA REST API."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession

from .const import (
    API_TIMEOUT,
    LOAD_MANAGEMENT_PATH,
    LOGIN_PATH,
    REFRESH_PATH,
    RFIDS_PATH,
    SERIAL_NUMBER_PATH,
    SESSIONS_PATH,
    VERSION_PATH,
    WALLBOXES_PATH,
)

_LOGGER = logging.getLogger(__name__)


class KebaApiError(Exception):
    """Base API error."""


class KebaAuthenticationError(KebaApiError):
    """Raised when authentication fails."""


@dataclass(slots=True)
class KebaApiConfig:
    """Runtime API configuration."""

    host: str
    port: int
    username: str
    password: str
    verify_ssl: bool

    @property
    def base_url(self) -> str:
        """Return the REST API base URL."""
        return f"https://{self.host}:{self.port}"


class KebaApiClient:
    """Minimal KEBA REST API client."""

    def __init__(self, session: ClientSession, config: KebaApiConfig) -> None:
        """Initialize the client."""
        self._session = session
        self._config = config
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    async def async_get_device_summary(self) -> dict[str, Any]:
        """Fetch the metadata and current wallbox state."""
        _LOGGER.debug("Fetching KEBA device summary from %s", self._config.base_url)
        version = await self.async_get_version()
        wallbox = await self.async_get_primary_wallbox()

        return {
            "api_version": version,
            "serial_number": wallbox.get("serialNumber"),
            "wallbox": wallbox,
        }

    async def async_get_version(self) -> str | None:
        """Fetch the REST API version."""
        data = await self._request("GET", VERSION_PATH, authenticated=False)
        return data if isinstance(data, str) else None

    async def async_get_device_serial(self) -> str | None:
        """Fetch the device serial number."""
        data = await self._request("GET", SERIAL_NUMBER_PATH, authenticated=False)
        return data if isinstance(data, str) else None

    async def async_get_primary_wallbox(self) -> dict[str, Any]:
        """Return the primary wallbox exposed by the device."""
        _LOGGER.debug("Resolving primary KEBA wallbox at %s", self._config.base_url)
        serial_number = await self.async_get_device_serial()
        wallboxes = await self.async_get_wallboxes()
        _LOGGER.debug(
            "KEBA API returned device serial %s and %s wallbox entries from %s",
            serial_number,
            len(wallboxes),
            self._config.base_url,
        )

        if not wallboxes:
            raise KebaApiError("No wallboxes returned by the API")

        if serial_number:
            for wallbox in wallboxes:
                if wallbox.get("serialNumber") == serial_number:
                    return wallbox

        if len(wallboxes) > 1:
            _LOGGER.warning(
                "More than one wallbox was returned by %s; using the first entry with serial %s",
                self._config.base_url,
                wallboxes[0].get("serialNumber"),
            )

        return wallboxes[0]

    async def async_get_wallboxes(self) -> list[dict[str, Any]]:
        """Fetch all wallboxes."""
        data = await self._request("GET", WALLBOXES_PATH, authenticated=True)
        wallboxes = data.get("wallboxes", [])
        return wallboxes if isinstance(wallboxes, list) else []

    async def async_get_wallbox(self, serial_number: str) -> dict[str, Any]:
        """Fetch a single wallbox, falling back to the wallbox list if needed."""
        try:
            return await self._request(
                "GET",
                f"{WALLBOXES_PATH}/{serial_number}",
                authenticated=True,
                log_http_error=False,
            )
        except KebaApiError as detail_error:
            try:
                wallboxes = await self.async_get_wallboxes()
            except KebaApiError as list_error:
                raise detail_error from list_error

            for wallbox in wallboxes:
                if wallbox.get("serialNumber") == serial_number:
                    _LOGGER.debug(
                        "KEBA wallbox detail endpoint failed for %s; using list response",
                        serial_number,
                    )
                    return wallbox

            raise detail_error

    async def async_get_sessions(
        self,
        serial_number: str,
        *,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch recent charging sessions for a wallbox."""
        data = await self._request(
            "GET",
            SESSIONS_PATH,
            authenticated=True,
            params={
                "offset": 0,
                "limit": limit,
                "orderField": "SESSION_START_DATE",
                "orderDir": "DESC",
                "filters": f"SOCKET_SERIAL_NUMBER={serial_number}",
            },
        )
        sessions = data.get("sessions", [])
        return sessions if isinstance(sessions, list) else []

    async def async_get_rfid_token(self, token_id: str) -> dict[str, Any]:
        """Fetch an RFID token by id."""
        return await self._request(
            "GET",
            f"{RFIDS_PATH}/{token_id}",
            authenticated=True,
        )

    async def async_start_charging(self, serial_number: str) -> None:
        """Start charging."""
        await self._request(
            "POST",
            f"{WALLBOXES_PATH}/{serial_number}/start-charging",
            authenticated=True,
        )

    async def async_stop_charging(self, serial_number: str) -> None:
        """Stop charging."""
        await self._request(
            "POST",
            f"{WALLBOXES_PATH}/{serial_number}/stop-charging",
            authenticated=True,
        )

    async def async_set_availability(self, serial_number: str, available: bool) -> None:
        """Set wallbox availability."""
        await self._request(
            "POST",
            f"{WALLBOXES_PATH}/{serial_number}/change-availability",
            authenticated=True,
            json={"available": available},
        )

    async def async_set_permanent_lock(self, serial_number: str, enabled: bool) -> None:
        """Enable or disable the permanent lock."""
        method = "POST" if enabled else "DELETE"
        await self._request(
            method,
            f"{WALLBOXES_PATH}/{serial_number}/permanently-lock",
            authenticated=True,
            json={} if enabled else None,
        )

    async def async_get_load_management_property(self, key: str) -> Any:
        """Fetch a load management configuration value."""
        data = await self._request(
            "GET",
            f"{LOAD_MANAGEMENT_PATH}/{key}",
            authenticated=True,
        )
        return _extract_config_value(data, key)

    async def async_set_max_available_current(self, milliamps: int) -> None:
        """Set the maximum available charging current."""
        await self._request(
            "PUT",
            LOAD_MANAGEMENT_PATH,
            authenticated=True,
            json={
                "configs": [
                    {
                        "key": "max_available_current",
                        "value": milliamps,
                    }
                ]
            },
        )

    async def async_login(self) -> None:
        """Authenticate against the REST API."""
        _LOGGER.debug("Requesting KEBA login token from %s", self._config.base_url)
        data = await self._request(
            "POST",
            LOGIN_PATH,
            authenticated=False,
            json={
                "username": self._config.username,
                "password": self._config.password,
            },
        )
        self._access_token = data.get("accessToken")
        self._refresh_token = data.get("refreshToken")

        if not self._access_token or not self._refresh_token:
            raise KebaAuthenticationError("Login did not return both JWT tokens")
        _LOGGER.debug("KEBA login succeeded for %s", self._config.base_url)

    async def async_refresh_access_token(self) -> None:
        """Refresh the access token."""
        if not self._refresh_token:
            raise KebaAuthenticationError("No refresh token available")

        _LOGGER.debug("Refreshing KEBA access token for %s", self._config.base_url)
        data = await self._request(
            "POST",
            REFRESH_PATH,
            authenticated=False,
            headers={"Authorization": f"Bearer {self._refresh_token}"},
        )

        self._access_token = data.get("accessToken")
        self._refresh_token = data.get("refreshToken", self._refresh_token)

        if not self._access_token:
            raise KebaAuthenticationError("Refresh did not return a new access token")
        _LOGGER.debug(
            "KEBA access token refresh succeeded for %s",
            self._config.base_url,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_on_auth_error: bool = True,
        log_http_error: bool = True,
    ) -> Any:
        """Perform an API request."""
        request_headers = dict(headers or {})
        url = f"{self._config.base_url}{path}"

        if authenticated:
            if not self._access_token:
                await self.async_login()
            request_headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            _LOGGER.debug(
                "Sending KEBA API request %s %s "
                "(authenticated=%s, verify_ssl=%s, timeout=%ss)",
                method,
                url,
                authenticated,
                self._config.verify_ssl,
                API_TIMEOUT,
            )
            async with self._session.request(
                method,
                url,
                headers=request_headers,
                json=json,
                params=params,
                ssl=self._config.verify_ssl,
                timeout=API_TIMEOUT,
            ) as response:
                _LOGGER.debug(
                    "Received KEBA API response HTTP %s for %s %s (content_type=%s)",
                    response.status,
                    method,
                    url,
                    response.content_type,
                )
                return await self._handle_response(
                    response,
                    method=method,
                    path=path,
                    authenticated=authenticated,
                    headers=headers,
                    json=json,
                    params=params,
                    retry_on_auth_error=retry_on_auth_error,
                    log_http_error=log_http_error,
                )
        except ClientError as err:
            _LOGGER.warning(
                "KEBA API request failed for %s %s: %s",
                method,
                url,
                err,
            )
            raise KebaApiError(f"Connection error: {err}") from err

    async def _handle_response(
        self,
        response: ClientResponse,
        *,
        method: str,
        path: str,
        authenticated: bool,
        headers: dict[str, str] | None,
        json: dict[str, Any] | None,
        params: dict[str, Any] | None,
        retry_on_auth_error: bool,
        log_http_error: bool,
    ) -> Any:
        """Handle the API response."""
        if response.status in (401, 403):
            _LOGGER.warning(
                "KEBA API authorization error HTTP %s for %s %s (authenticated=%s)",
                response.status,
                method,
                path,
                authenticated,
            )
            if not authenticated:
                raise KebaAuthenticationError("Authentication failed")

            if retry_on_auth_error and self._refresh_token:
                _LOGGER.debug(
                    "Retrying KEBA request after token refresh: %s %s",
                    method,
                    path,
                )
                await self.async_refresh_access_token()
                return await self._request(
                    method,
                    path,
                    authenticated=authenticated,
                    headers=headers,
                    json=json,
                    params=params,
                    retry_on_auth_error=False,
                )

            self._access_token = None
            self._refresh_token = None
            _LOGGER.debug(
                "Retrying KEBA request after fresh login: %s %s",
                method,
                path,
            )
            await self.async_login()
            return await self._request(
                method,
                path,
                authenticated=authenticated,
                headers=headers,
                json=json,
                params=params,
                retry_on_auth_error=False,
            )

        if response.status >= 400:
            payload = await response.text()
            log_method = _LOGGER.warning if log_http_error else _LOGGER.debug
            log_method(
                "KEBA API returned HTTP %s for %s %s: %s",
                response.status,
                method,
                path,
                payload,
            )
            raise KebaApiError(f"HTTP {response.status}: {payload}")

        if response.content_type == "application/json":
            return await response.json()

        text = await response.text()
        return text.strip().strip('"')


def _extract_config_value(data: Any, key: str) -> Any:
    """Extract a configuration value from a KEBA config response."""
    if not isinstance(data, dict):
        return None

    configs = data.get("configs")
    if not isinstance(configs, list):
        return None

    for item in configs:
        if isinstance(item, dict) and item.get("key") in (key, None):
            return item.get("value")

    return None
