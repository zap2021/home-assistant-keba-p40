"""Sensor platform for the KEBA integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KebaDataUpdateCoordinator
from .entity import KebaEntity


@dataclass(frozen=True, kw_only=True)
class KebaSensorDescription(SensorEntityDescription):
    """Describe a KEBA sensor."""

    value_key: str


SENSORS: tuple[KebaSensorDescription, ...] = (
    KebaSensorDescription(
        key="charging_power",
        translation_key="charging_power",
        name="Charging Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_key="charging_power",
    ),
    KebaSensorDescription(
        key="energy_total",
        translation_key="energy_total",
        name="Total Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_key="energy_total",
    ),
    KebaSensorDescription(
        key="current_offered",
        translation_key="current_offered",
        name="Current Offered",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_key="current_offered",
    ),
    KebaSensorDescription(
        key="temperature",
        translation_key="temperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_key="temperature",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KEBA sensors from a config entry."""
    coordinator: KebaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(KebaSensor(coordinator, description) for description in SENSORS)


class KebaSensor(KebaEntity, SensorEntity):
    """Representation of a KEBA sensor."""

    entity_description: KebaSensorDescription

    def __init__(
        self,
        coordinator: KebaDataUpdateCoordinator,
        description: KebaSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        return self.coordinator.data.get(self.entity_description.value_key)
