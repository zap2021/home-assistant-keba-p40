"""Data coordinator for the KEBA integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KebaApiClient, KebaApiConfig
from .const import CONF_SCAN_INTERVAL, CONF_SERIAL_NUMBER, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class KebaDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate KEBA data updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data[CONF_PORT]
        self.serial_number: str = entry.data[CONF_SERIAL_NUMBER]
        update_interval = timedelta(seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL.seconds))
        session = async_get_clientsession(
            hass,
            verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
        )
        self.api = KebaApiClient(
            session,
            KebaApiConfig(
                host=self.host,
                port=self.port,
                username=entry.data[CONF_USERNAME],
                password=entry.data[CONF_PASSWORD],
                verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
            ),
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        try:
            return await self._async_fetch_status()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with KEBA wallbox: {err}") from err

    async def _async_fetch_status(self) -> dict[str, Any]:
        """Fetch status information from the REST API."""
        wallbox = await self.api.async_get_wallbox(self.serial_number)
        version = await self.api.async_get_version()
        meter = wallbox.get("meter") or {}

        return {
            "api_version": version,
            "serial_number": wallbox.get("serialNumber", self.serial_number),
            "wallbox": wallbox,
            "state": wallbox.get("state"),
            "charging_power": _milliwatts_to_watts(meter.get("totalActivePower")),
            "energy_total": _milliwatt_hours_to_kwh(meter.get("meterValue")),
            "current_offered": _milliamps_to_amps(meter.get("currentOffered")),
            "temperature": _centicelsius_to_celsius(meter.get("temperature")),
            "vehicle_plugged": wallbox.get("vehiclePlugged"),
            "session_active": wallbox.get("sessionActive"),
            "authorization_enabled": wallbox.get("authorizationEnabled"),
            "available": wallbox.get("state") != "UNAVAILABLE",
            "permanently_locked": wallbox.get("permanentlyLocked"),
        }


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
