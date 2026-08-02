"""Switch platform for the KEBA integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KebaDataUpdateCoordinator
from .entity import KebaEntity

KebaCommand = Callable[[KebaDataUpdateCoordinator], Awaitable[None]]


@dataclass(frozen=True, kw_only=True)
class KebaSwitchDescription(SwitchEntityDescription):
    """Describe a KEBA switch."""

    value_key: str
    turn_on_fn: KebaCommand
    turn_off_fn: KebaCommand


SWITCHES: tuple[KebaSwitchDescription, ...] = (
    KebaSwitchDescription(
        key="charging",
        translation_key="charging",
        name="Charging",
        value_key="session_active",
        turn_on_fn=lambda coordinator: coordinator.api.async_start_charging(coordinator.serial_number),
        turn_off_fn=lambda coordinator: coordinator.api.async_stop_charging(coordinator.serial_number),
    ),
    KebaSwitchDescription(
        key="availability",
        translation_key="availability",
        name="Availability",
        value_key="available",
        turn_on_fn=lambda coordinator: coordinator.api.async_set_availability(coordinator.serial_number, True),
        turn_off_fn=lambda coordinator: coordinator.api.async_set_availability(coordinator.serial_number, False),
    ),
    KebaSwitchDescription(
        key="permanent_lock",
        translation_key="permanent_lock",
        name="Permanent Lock",
        value_key="permanently_locked",
        turn_on_fn=lambda coordinator: coordinator.api.async_set_permanent_lock(coordinator.serial_number, True),
        turn_off_fn=lambda coordinator: coordinator.api.async_set_permanent_lock(coordinator.serial_number, False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KEBA switches from a config entry."""
    coordinator: KebaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(KebaSwitch(coordinator, description) for description in SWITCHES)


class KebaSwitch(KebaEntity, SwitchEntity):
    """Representation of a KEBA switch."""

    entity_description: KebaSwitchDescription

    def __init__(
        self,
        coordinator: KebaDataUpdateCoordinator,
        description: KebaSwitchDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the current state."""
        value = self.coordinator.data.get(self.entity_description.value_key)
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self.entity_description.turn_on_fn(self.coordinator)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self.entity_description.turn_off_fn(self.coordinator)
        await self.coordinator.async_request_refresh()
