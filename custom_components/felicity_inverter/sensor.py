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


def _diagnostic_energy_description(
    key: str,
    name: str,
    *,
    total_increasing: bool = False,
) -> FelicitySensorDescription:
    """Build a diagnostic energy sensor description."""
    return FelicitySensorDescription(
        key=key,
        name=name,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING if total_increasing else None,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:counter",
    )


ENERGY_COUNTER_SENSOR_DESCRIPTIONS: tuple[FelicitySensorDescription, ...] = tuple(
    _diagnostic_energy_description(
        key=f"{prefix}_{period_key}",
        name=f"{name} {period_label}",
        total_increasing=period_key == "total",
    )
    for prefix, name in (
        ("pv_yield_energy", "PV Yield Energy"),
        ("load_consumption_energy", "Load Consumption Energy"),
        ("grid_export_energy", "Grid Export Energy"),
        ("grid_import_energy", "Grid Import Energy"),
        ("battery_charge_energy", "Battery Charge Energy"),
        ("battery_discharge_energy", "Battery Discharge Energy"),
    )
    for period_key, period_label in (
        ("daily", "Daily"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
        ("total", "Total"),
    )
)


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
        key="battery_state_of_health",
        name="Battery State of Health",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:battery-heart-variant",
    ),
    FelicitySensorDescription(
        key="battery_capacity",
        name="Battery Capacity",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:battery-unknown",
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
        key="battery_charge_status",
        name="Battery Charge Status",
        icon="mdi:battery-sync",
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
        key="pv_total_power",
        name="PV Total Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    *tuple(
        FelicitySensorDescription(
            key=f"pv{index}_voltage",
            name=f"PV{index} Voltage",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
            icon="mdi:solar-panel",
        )
        for index in range(1, 4)
    ),
    *tuple(
        FelicitySensorDescription(
            key=f"pv{index}_current",
            name=f"PV{index} Current",
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
            icon="mdi:current-dc",
        )
        for index in range(1, 4)
    ),
    *tuple(
        FelicitySensorDescription(
            key=f"pv{index}_power",
            name=f"PV{index} Power",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:solar-power",
        )
        for index in range(1, 4)
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
        key="grid_power",
        name="Grid Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
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
        key="grid_apparent_power",
        name="Grid Apparent Power",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-triangle",
    ),
    FelicitySensorDescription(
        key="grid_total_power",
        name="Grid Total Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
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
        key="load_apparent_power",
        name="Load Apparent Power",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-triangle",
    ),
    FelicitySensorDescription(
        key="load_total_power",
        name="Load Total Power",
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
        key="generator_frequency",
        name="Generator Frequency",
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:sine-wave",
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
        key="generator_apparent_power",
        name="Generator Apparent Power",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-triangle",
    ),
    FelicitySensorDescription(
        key="generator_total_power",
        name="Generator Total Power",
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
        key="smart_load_frequency",
        name="Smart Load Frequency",
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:sine-wave",
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
        key="smart_load_apparent_power",
        name="Smart Load Apparent Power",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-triangle",
    ),
    FelicitySensorDescription(
        key="smart_load_total_power",
        name="Smart Load Total Power",
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
        key="transformer_temperature",
        name="Transformer Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="heatsink_temperature",
        name="Heatsink Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="ambient_temperature",
        name="Ambient Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="bus_voltage",
        name="Bus Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="bus_negative_voltage",
        name="Bus Negative Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
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
    *ENERGY_COUNTER_SENSOR_DESCRIPTIONS,
    FelicitySensorDescription(
        key="inverter_mode",
        name="Inverter Mode",
        icon="mdi:home-switch",
    ),
    FelicitySensorDescription(
        key="communication_protocol_version",
        name="Communication Protocol Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:information-outline",
    ),
    FelicitySensorDescription(
        key="device_type",
        name="Device Type",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
    ),
    FelicitySensorDescription(
        key="device_subtype",
        name="Device Subtype",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
    ),
    FelicitySensorDescription(
        key="last_update",
        name="Payload Timestamp",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-outline",
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
        key="power_flow_status_raw",
        name="Power Flow Status Raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:vector-polyline",
    ),
    FelicitySensorDescription(
        key="power_flow_secondary_status_raw",
        name="Power Flow Secondary Status Raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:vector-polyline-plus",
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
        key="bms_firmware_version",
        name="BMS Firmware Version",
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
        key="bms_device_serial",
        name="BMS Serial",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
    ),
    FelicitySensorDescription(
        key="bms_inverter_serial",
        name="BMS Inverter Serial",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
    ),
    FelicitySensorDescription(
        key="bms_modbus_address",
        name="BMS Modbus Address",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:counter",
    ),
    FelicitySensorDescription(
        key="bms_last_update",
        name="BMS Payload Timestamp",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-outline",
    ),
    FelicitySensorDescription(
        key="bms_count",
        name="BMS Count",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-multiple",
    ),
    FelicitySensorDescription(
        key="wifi_status",
        name="WiFi Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wifi-check",
    ),
    FelicitySensorDescription(
        key="bms_communication_status",
        name="BMS Communication Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:lan-connect",
    ),
    FelicitySensorDescription(
        key="bms_registration_status",
        name="BMS Registration Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:shield-check",
    ),
    FelicitySensorDescription(
        key="bms_global_status",
        name="BMS Global Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:shield-sync",
    ),
    FelicitySensorDescription(
        key="charge_source_priority",
        name="Charge Source Priority",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:source-branch",
    ),
    FelicitySensorDescription(
        key="max_ac_charge_current_limit",
        name="Max AC Charge Current Limit",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:current-ac",
    ),
    FelicitySensorDescription(
        key="smart_port_status",
        name="Smart Port Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:power-plug",
    ),
    FelicitySensorDescription(
        key="system_power_status",
        name="System Power Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:power-settings",
    ),
    FelicitySensorDescription(
        key="bms_fault_code",
        name="BMS Fault Code",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-octagon",
    ),
    FelicitySensorDescription(
        key="bms_warning_code",
        name="BMS Warning Code",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert",
    ),
    FelicitySensorDescription(
        key="bms_state",
        name="BMS State",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-lock",
    ),
    FelicitySensorDescription(
        key="bms_pack_voltage",
        name="BMS Pack Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-high",
    ),
    FelicitySensorDescription(
        key="bms_pack_current",
        name="BMS Pack Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="bms_pack_soc",
        name="BMS Pack SOC",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-medium",
    ),
    FelicitySensorDescription(
        key="bms_pack_state_of_health",
        name="BMS Pack State of Health",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-heart-variant",
    ),
    FelicitySensorDescription(
        key="bms_total_capacity",
        name="BMS Total Capacity",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-unknown",
    ),
    FelicitySensorDescription(
        key="bms_max_cell_voltage",
        name="BMS Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-plus-variant",
    ),
    FelicitySensorDescription(
        key="bms_min_cell_voltage",
        name="BMS Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-minus-variant",
    ),
    FelicitySensorDescription(
        key="bms_max_cell_temperature",
        name="BMS Max Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer-high",
    ),
    FelicitySensorDescription(
        key="bms_min_cell_temperature",
        name="BMS Min Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer-low",
    ),
    FelicitySensorDescription(
        key="bms_parallel_count",
        name="BMS Parallel Count",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-multiple",
    ),
    FelicitySensorDescription(
        key="bms_hardware_config",
        name="BMS Hardware Config",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
    ),
    FelicitySensorDescription(
        key="bms_charge_voltage_limit",
        name="BMS Charge Voltage Limit",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-charging-high",
    ),
    FelicitySensorDescription(
        key="bms_discharge_voltage_limit",
        name="BMS Discharge Voltage Limit",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-arrow-down",
    ),
    FelicitySensorDescription(
        key="bms_charge_current_limit",
        name="BMS Charge Current Limit",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="bms_discharge_current_limit",
        name="BMS Discharge Current Limit",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:current-dc",
    ),
    FelicitySensorDescription(
        key="bms_temperature_1",
        name="BMS Temperature 1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="bms_temperature_2",
        name="BMS Temperature 2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer",
    ),
    FelicitySensorDescription(
        key="raw_json_payload",
        name="Raw JSON Payload",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:code-json",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Felicity sensors from a config entry."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime.coordinator

    async_add_entities(
        [FelicitySensor(coordinator, entry, description) for description in SENSOR_DESCRIPTIONS]
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
