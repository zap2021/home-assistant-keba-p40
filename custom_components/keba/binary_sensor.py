"""Binary sensors for the KEBA integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KebaDataUpdateCoordinator
from .entity import KebaEntity


@dataclass(frozen=True, kw_only=True)
class KebaBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a KEBA binary sensor."""

    value_key: str


BINARY_SENSORS: tuple[KebaBinarySensorDescription, ...] = (
    KebaBinarySensorDescription(
        key="vehicle_plugged",
        translation_key="vehicle_plugged",
        name="Vehicle Plugged",
        device_class=BinarySensorDeviceClass.PLUG,
        value_key="vehicle_plugged",
    ),
    KebaBinarySensorDescription(
        key="session_active",
        translation_key="session_active",
        name="Session Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_key="session_active",
    ),
    KebaBinarySensorDescription(
        key="authorization_enabled",
        translation_key="authorization_enabled",
        name="Authorization Enabled",
        value_key="authorization_enabled",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KEBA binary sensors from a config entry."""
    coordinator: KebaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(KebaBinarySensor(coordinator, description) for description in BINARY_SENSORS)


class KebaBinarySensor(KebaEntity, BinarySensorEntity):
    """Representation of a KEBA binary sensor."""

    entity_description: KebaBinarySensorDescription

    def __init__(
        self,
        coordinator: KebaDataUpdateCoordinator,
        description: KebaBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the current state."""
        value = self.coordinator.data.get(self.entity_description.value_key)
        return value if isinstance(value, bool) else None
