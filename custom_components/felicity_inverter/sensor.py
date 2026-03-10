from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import FelicityCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class FelicitySensorDescription(SensorEntityDescription):
    """Extended sensor description for Felicity telemetry."""


SENSOR_DESCRIPTIONS: tuple[FelicitySensorDescription, ...] = (
    FelicitySensorDescription(
        key="battery_soc",
        name="Battery SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:battery",
    ),
    FelicitySensorDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:battery-high",
    ),
    FelicitySensorDescription(
        key="battery_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="battery_power",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-up-outline",
    ),
    FelicitySensorDescription(
        key="battery_charge_power",
        name="Battery Charge Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
    ),
    FelicitySensorDescription(
        key="battery_discharge_power",
        name="Battery Discharge Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-minus",
    ),
    FelicitySensorDescription(
        key="battery_charge_current",
        name="Battery Charge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="battery_discharge_current",
        name="Battery Discharge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="battery_temperature",
        name="Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:battery-heart-variant",
    ),
    FelicitySensorDescription(
        key="pv_voltage",
        name="PV Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:solar-panel",
    ),
    FelicitySensorDescription(
        key="pv_current",
        name="PV Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="pv_power",
        name="PV Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    FelicitySensorDescription(
        key="grid_voltage",
        name="Grid Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:transmission-tower",
    ),
    FelicitySensorDescription(
        key="grid_current",
        name="Grid Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:current-ac",
    ),
    FelicitySensorDescription(
        key="grid_frequency",
        name="Grid Frequency",
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:sine-wave",
    ),
    FelicitySensorDescription(
        key="grid_import_power",
        name="Grid Import Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower-import",
    ),
    FelicitySensorDescription(
        key="grid_export_power",
        name="Grid Export Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower-export",
    ),
    FelicitySensorDescription(
        key="load_voltage",
        name="Load Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:home-lightning-bolt",
    ),
    FelicitySensorDescription(
        key="load_current",
        name="Load Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:current-ac",
    ),
    FelicitySensorDescription(
        key="output_frequency",
        name="Output Frequency",
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:sine-wave",
    ),
    FelicitySensorDescription(
        key="load_power",
        name="Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-lightning-bolt-outline",
    ),
    FelicitySensorDescription(
        key="generator_voltage",
        name="Generator Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:engine",
    ),
    FelicitySensorDescription(
        key="generator_current",
        name="Generator Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:engine",
    ),
    FelicitySensorDescription(
        key="generator_power",
        name="Generator Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:engine",
    ),
    FelicitySensorDescription(
        key="smart_load_voltage",
        name="Smart Load Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:lightning-bolt-circle",
    ),
    FelicitySensorDescription(
        key="smart_load_current",
        name="Smart Load Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:lightning-bolt-circle",
    ),
    FelicitySensorDescription(
        key="smart_load_power",
        name="Smart Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt-circle",
    ),
    FelicitySensorDescription(
        key="inverter_temperature",
        name="Inverter Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="bus_voltage",
        name="Bus Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="load_percent",
        name="Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:gauge",
    ),
    FelicitySensorDescription(
        key="pv_to_load_power",
        name="PV to Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-right-bold-circle",
    ),
    FelicitySensorDescription(
        key="pv_to_battery_power",
        name="PV to Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-down-bold-circle",
    ),
    FelicitySensorDescription(
        key="pv_to_grid_power",
        name="PV to Grid Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-up-bold-circle",
    ),
    FelicitySensorDescription(
        key="battery_to_load_power",
        name="Battery to Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-down-outline",
    ),
    FelicitySensorDescription(
        key="grid_to_load_power",
        name="Grid to Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
    ),
    FelicitySensorDescription(
        key="self_consumption_percent",
        name="Self Consumption",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:percent",
    ),
    FelicitySensorDescription(
        key="battery_roundtrip_efficiency",
        name="Battery Roundtrip Efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:battery-sync",
    ),
    FelicitySensorDescription(
        key="inverter_throughput_energy",
        name="Inverter Throughput Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        icon="mdi:counter",
    ),
    FelicitySensorDescription(
        key="inverter_mode",
        name="Inverter Mode",
        icon="mdi:home-switch",
    ),
    FelicitySensorDescription(
        key="inverter_warning_code",
        name="Inverter Warning Code",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert",
    ),
    FelicitySensorDescription(
        key="inverter_fault_code",
        name="Inverter Fault Code",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-octagon",
    ),
    FelicitySensorDescription(
        key="device_serial",
        name="Device Serial",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
    ),
    FelicitySensorDescription(
        key="wifi_serial",
        name="WiFi Serial",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wifi",
    ),
    FelicitySensorDescription(
        key="firmware_version",
        name="Firmware Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
    ),
    FelicitySensorDescription(
        key="device_software_version",
        name="Device Software Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
    ),
    FelicitySensorDescription(
        key="device_hardware_version",
        name="Device Hardware Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
    ),
    FelicitySensorDescription(
        key="raw_json_payload",
        name="Raw JSON Payload",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:code-json",
    ),
)


CELL_SENSOR_DESCRIPTIONS: tuple[FelicitySensorDescription, ...] = tuple(
    [
        FelicitySensorDescription(
            key=f"battery_cell_{index}_voltage",
            name=f"Battery Cell {index} Voltage",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=3,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:battery-outline",
        )
        for index in range(1, 17)
    ]
    + [
        FelicitySensorDescription(
            key=f"battery_cell_{index}_temperature",
            name=f"Battery Cell {index} Temperature",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:thermometer",
        )
        for index in range(1, 9)
    ]
)


ALL_SENSOR_DESCRIPTIONS = SENSOR_DESCRIPTIONS + CELL_SENSOR_DESCRIPTIONS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Felicity sensors from a config entry."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime.coordinator

    async_add_entities(
        [FelicitySensor(coordinator, entry, description) for description in ALL_SENSOR_DESCRIPTIONS]
    )


class FelicitySensor(FelicityCoordinatorEntity, SensorEntity):
    """Representation of a normalized Felicity sensor."""

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: FelicitySensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Return whether the entity is available."""
        if not super().available:
            return False

        data = self.coordinator.data or {}
        key = self.entity_description.key
        if key == "raw_json_payload":
            return bool(data.get("_raw_payloads"))
        return key in data and data.get(key) is not None

    @property
    def native_value(self) -> Any:
        """Return the current normalized sensor value."""
        return (self.coordinator.data or {}).get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose diagnostic attributes for the raw payload entity."""
        data = self.coordinator.data or {}
        if self.entity_description.key != "raw_json_payload":
            return None

        return {
            "last_update": data.get("last_update"),
            "raw_payloads": data.get("_raw_payloads"),
            "raw_objects": data.get("_raw_objects"),
            "raw_inverter": data.get("_raw_inverter"),
            "raw_bms": data.get("_raw_bms"),
            "raw_settings": data.get("_raw_settings"),
            "raw_energy_counters": data.get("_raw_energy_counters"),
            "ac_layouts": data.get("_ac_layouts"),
        }
