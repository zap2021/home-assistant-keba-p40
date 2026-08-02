"""Data coordinator for the KEBA integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KebaApiClient, KebaApiConfig, KebaApiError
from .const import CONF_SCAN_INTERVAL, CONF_SERIAL_NUMBER, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)
ACTIVE_SESSION_STATUSES = {"INITIATED", "PWM_CHARGING", "BLOCKED"}


class KebaDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate KEBA data updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self._hass = hass
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data[CONF_PORT]
        self.serial_number: str = entry.data.get(CONF_SERIAL_NUMBER, "")
        self.device_identifier: str = (
            entry.unique_id or self.serial_number or entry.entry_id
        )
        update_interval = timedelta(
            seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL.seconds)
        )
        verify_ssl = entry.data.get(CONF_VERIFY_SSL, False)
        _LOGGER.debug(
            "Initializing KEBA coordinator for entry %s (%s:%s, verify_ssl=%s, "
            "scan_interval=%s, has_serial=%s)",
            entry.entry_id,
            self.host,
            self.port,
            verify_ssl,
            update_interval,
            bool(self.serial_number),
        )
        session = async_get_clientsession(
            hass,
            verify_ssl=verify_ssl,
        )
        self.api = KebaApiClient(
            session,
            KebaApiConfig(
                host=self.host,
                port=self.port,
                username=entry.data[CONF_USERNAME],
                password=entry.data[CONF_PASSWORD],
                verify_ssl=verify_ssl,
            ),
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.data = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        try:
            data = await self._async_fetch_status()
            _LOGGER.debug(
                "KEBA data update succeeded for %s:%s (serial=%s, state=%s)",
                self.host,
                self.port,
                data.get("serial_number"),
                data.get("state"),
            )
            return data
        except Exception as err:
            if not self.serial_number:
                _LOGGER.warning(
                    "KEBA connection setup failed for %s:%s: %s",
                    self.host,
                    self.port,
                    err,
                )
            else:
                _LOGGER.debug(
                    "KEBA data update failed for %s:%s (serial=%s): %s",
                    self.host,
                    self.port,
                    self.serial_number,
                    err,
                    exc_info=True,
                )
            raise UpdateFailed(f"Error communicating with KEBA wallbox: {err}") from err

    async def _async_fetch_status(self) -> dict[str, Any]:
        """Fetch status information from the REST API."""
        if self.serial_number:
            _LOGGER.debug(
                "Fetching KEBA wallbox status from %s:%s using serial %s",
                self.host,
                self.port,
                self.serial_number,
            )
            wallbox = await self.api.async_get_wallbox(self.serial_number)
            version = await self.api.async_get_version()
        else:
            _LOGGER.info(
                "No KEBA serial number saved yet; discovering device at %s:%s",
                self.host,
                self.port,
            )
            summary = await self.api.async_get_device_summary()
            wallbox = summary["wallbox"]
            version = summary["api_version"]
            self._store_discovered_device(wallbox, summary["serial_number"])
            _LOGGER.info(
                "Discovered KEBA device at %s:%s (serial=%s, api_version=%s)",
                self.host,
                self.port,
                self.serial_number,
                version,
            )

        meter = wallbox.get("meter") or {}
        rfid_data = await self._async_fetch_current_rfid(wallbox)
        max_available_current = await self._async_fetch_max_available_current()

        return {
            "api_version": version,
            "serial_number": wallbox.get("serialNumber", self.serial_number),
            "wallbox": wallbox,
            "state": wallbox.get("state"),
            "max_current": _milliamps_to_amps(wallbox.get("maxCurrent")),
            "max_available_current": _milliamps_to_amps(max_available_current),
            "charging_power": _milliwatts_to_watts(meter.get("totalActivePower")),
            "energy_total": _milliwatt_hours_to_kwh(meter.get("meterValue")),
            "current_offered": _milliamps_to_amps(meter.get("currentOffered")),
            "temperature": _centicelsius_to_celsius(meter.get("temperature")),
            "vehicle_plugged": wallbox.get("vehiclePlugged"),
            "session_active": wallbox.get("sessionActive"),
            "authorization_enabled": wallbox.get("authorizationEnabled"),
            "available": wallbox.get("state") != "UNAVAILABLE",
            "permanently_locked": wallbox.get("permanentlyLocked"),
            **rfid_data,
        }

    async def _async_fetch_max_available_current(self) -> Any:
        """Fetch the REST load-management current limit."""
        try:
            return await self.api.async_get_load_management_property(
                "max_available_current"
            )
        except KebaApiError as err:
            _LOGGER.debug(
                "Unable to fetch KEBA max available current from %s:%s: %s",
                self.host,
                self.port,
                err,
            )
            return None

    async def _async_fetch_current_rfid(self, wallbox: dict[str, Any]) -> dict[str, Any]:
        """Fetch the RFID token that authorized the currently active session."""
        result: dict[str, Any] = {
            "current_rfid_card": None,
            "current_rfid_card_attributes": {},
        }

        if not wallbox.get("sessionActive"):
            return result

        try:
            sessions = await self.api.async_get_sessions(self.serial_number)
        except KebaApiError as err:
            _LOGGER.debug(
                "Unable to fetch KEBA sessions for RFID lookup on %s:%s: %s",
                self.host,
                self.port,
                err,
            )
            return result

        active_session = _find_active_session(sessions)
        if not active_session:
            _LOGGER.debug(
                "KEBA wallbox %s reports an active session, but no active session "
                "entry was returned",
                self.serial_number,
            )
            return result

        token_id = active_session.get("tokenId")
        attributes = _compact_dict(
            {
                "session_id": active_session.get("id"),
                "session_status": active_session.get("status"),
                "session_start": active_session.get("startDate"),
                "token_id": token_id,
                "wallbox_serial_number": active_session.get("wallboxSerialNumber"),
            }
        )

        token: dict[str, Any] = {}
        if token_id:
            try:
                token = await self.api.async_get_rfid_token(str(token_id))
            except KebaApiError as err:
                _LOGGER.debug(
                    "Unable to fetch KEBA RFID token details for active session %s: %s",
                    active_session.get("id"),
                    err,
                )

        if token:
            attributes.update(
                _compact_dict(
                    {
                        "token_name": token.get("name"),
                        "token_status": token.get("status"),
                        "token_details": token.get("details"),
                        "token_used_date": token.get("usedDate"),
                        "token_expiry_date": token.get("expiryDate"),
                        "token_changed_date": token.get("changedDate"),
                    }
                )
            )

        result["current_rfid_card"] = token.get("name") or token_id
        result["current_rfid_card_attributes"] = attributes
        return result

    def _store_discovered_device(
        self,
        wallbox: dict[str, Any],
        serial_number: str | None,
    ) -> None:
        """Persist device metadata discovered during the first connection test."""
        if not serial_number:
            raise KebaApiError("No serial number returned by the API")

        self.serial_number = serial_number
        _LOGGER.info(
            "Storing discovered KEBA serial number %s for config entry %s",
            serial_number,
            self.entry.entry_id,
        )
        self._hass.config_entries.async_update_entry(
            self.entry,
            data={
                **self.entry.data,
                CONF_SERIAL_NUMBER: serial_number,
            },
            title=wallbox.get("alias") or self.entry.title,
        )


def _milliwatts_to_watts(value: Any) -> float | None:
    """Convert mW to W."""
    if value is None:
        return None
    return round(float(value) / 1000, 2)


def _milliwatt_hours_to_kwh(value: Any) -> float | None:
    """Convert mWh to kWh."""
    if value is None:
        return None
    return round(float(value) / 1_000_000, 3)


def _milliamps_to_amps(value: Any) -> float | None:
    """Convert mA to A."""
    if value is None:
        return None
    return round(float(value) / 1000, 2)


def _centicelsius_to_celsius(value: Any) -> float | None:
    """Convert hundredths of a degree Celsius to Celsius."""
    if value is None:
        return None
    return round(float(value) / 100, 2)


def _find_active_session(sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the most recent non-closed session."""
    for session in sessions:
        if session.get("status") in ACTIVE_SESSION_STATUSES:
            return session
    return None


def _compact_dict(values: dict[str, Any]) -> dict[str, Any]:
    """Return a copy without empty values."""
    return {
        key: value
        for key, value in values.items()
        if value is not None and value != ""
    }
