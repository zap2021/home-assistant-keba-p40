"""Base entities for the KEBA integration."""

from __future__ import annotations

from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import KebaDataUpdateCoordinator


class KebaEntity(CoordinatorEntity[KebaDataUpdateCoordinator]):
    """Base KEBA entity."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        wallbox = self.coordinator.data.get("wallbox", {})

        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.serial_number)},
            manufacturer="KEBA",
            model=wallbox.get("model", "Wallbox"),
            model_id=wallbox.get("number"),
            name=wallbox.get("alias") or self.coordinator.entry.data.get(CONF_NAME, DEFAULT_NAME),
            serial_number=self.coordinator.data.get("serial_number"),
            sw_version=wallbox.get("firmwareVersion"),
            hw_version=wallbox.get("firmwareVersionMetering"),
        )
