from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import FelicityCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class FelicityBinarySensorDescription(BinarySensorEntityDescription):
    """Description for a normalized Felicity binary sensor."""


BINARY_SENSOR_DESCRIPTIONS: tuple[FelicityBinarySensorDescription, ...] = (
    FelicityBinarySensorDescription(
        key="fault_active",
        name="Fault Active",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicityBinarySensorDescription(
        key="warning_active",
        name="Warning Active",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicityBinarySensorDescription(
        key="grid_connected",
        name="Grid Connected",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FelicityBinarySensorDescription(
        key="battery_present",
        name="Battery Present",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Felicity binary sensors from a config entry."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime.coordinator

    async_add_entities(
        [
            FelicityBinarySensor(coordinator, entry, description)
            for description in BINARY_SENSOR_DESCRIPTIONS
        ]
    )


class FelicityBinarySensor(FelicityCoordinatorEntity, BinarySensorEntity):
    """Representation of a normalized Felicity binary sensor."""

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: FelicityBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Return whether the binary sensor is available."""
        if not super().available:
            return False

        data = self.coordinator.data or {}
        key = self.entity_description.key
        if key == "fault_active":
            return data.get("inverter_fault_code") is not None
        if key == "warning_active":
            return data.get("inverter_warning_code") is not None
        if key == "grid_connected":
            return data.get("grid_voltage") is not None
        if key == "battery_present":
            return data.get("battery_voltage") is not None
        return False

    @property
    def is_on(self) -> bool | None:
        """Return the current state of the binary sensor."""
        data: dict[str, Any] = self.coordinator.data or {}
        key = self.entity_description.key

        if key == "fault_active":
            value = data.get("inverter_fault_code")
            return None if value is None else value != 0

        if key == "warning_active":
            value = data.get("inverter_warning_code")
            return None if value is None else value != 0

        if key == "grid_connected":
            value = data.get("grid_voltage")
            return None if value is None else float(value) > 50.0

        if key == "battery_present":
            value = data.get("battery_voltage")
            return None if value is None else float(value) > 10.0

        return None
