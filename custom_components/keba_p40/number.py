"""Number platform for the KEBA integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KebaDataUpdateCoordinator
from .entity import KebaEntity


@dataclass(frozen=True, kw_only=True)
class KebaNumberDescription(NumberEntityDescription):
    """Describe a KEBA number entity."""

    value_key: str


NUMBERS: tuple[KebaNumberDescription, ...] = (
    KebaNumberDescription(
        key="max_available_current",
        translation_key="max_available_current",
        name="Maximum Available Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=6,
        native_step=1,
        value_key="max_available_current",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KEBA numbers from a config entry."""
    coordinator: KebaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(KebaNumber(coordinator, description) for description in NUMBERS)


class KebaNumber(KebaEntity, NumberEntity):
    """Representation of a KEBA number entity."""

    entity_description: KebaNumberDescription

    def __init__(
        self,
        coordinator: KebaDataUpdateCoordinator,
        description: KebaNumberDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the current number value."""
        return self.coordinator.data.get(self.entity_description.value_key)

    @property
    def native_max_value(self) -> float:
        """Return the maximum current supported by the wallbox."""
        max_current = self.coordinator.data.get("max_current")
        if isinstance(max_current, (int, float)) and max_current > 0:
            return float(max_current)
        return 32.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the maximum available current."""
        await self.coordinator.api.async_set_max_available_current(round(value * 1000))
        await self.coordinator.async_request_refresh()
