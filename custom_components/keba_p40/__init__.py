"""The KEBA integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_VERIFY_SSL, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import KebaDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KEBA from a config entry."""
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, False)

    _LOGGER.info(
        "Setting up KEBA config entry %s for %s:%s (verify_ssl=%s)",
        entry.entry_id,
        host,
        port,
        verify_ssl,
    )
    coordinator = KebaDataUpdateCoordinator(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    _LOGGER.info("Running initial KEBA connection check for %s:%s", host, port)
    await coordinator.async_refresh()
    if coordinator.last_update_success:
        _LOGGER.info("Initial KEBA connection check succeeded for %s:%s", host, port)
    else:
        _LOGGER.warning(
            "Initial KEBA connection check failed for %s:%s; entities will be "
            "set up as unavailable and retried on the next update",
            host,
            port,
        )

    _LOGGER.debug(
        "Forwarding KEBA config entry %s to platforms: %s",
        entry.entry_id,
        PLATFORMS,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Finished KEBA config entry setup for %s:%s", host, port)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading KEBA config entry %s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
