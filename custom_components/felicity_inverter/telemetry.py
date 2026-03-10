from __future__ import annotations

from typing import Any

from .api import RawPollData, merge_json_objects
from .protocol import BMS_TYPE, INVERTER_TYPE

MODE_MAP: dict[int, str] = {
    0: "standby",
    1: "line",
    2: "battery",
    3: "hybrid",
    4: "bypass",
}

BATTERY_CHARGE_STATUS_MAP: dict[int, str] = {
    0: "idle_or_discharge",
    1: "charge",
}

WIFI_STATUS_MAP: dict[int, str] = {
    2: "cloud_connected",
}

BMS_COMMUNICATION_STATUS_MAP: dict[int, str] = {
    1: "active",
}

BMS_REGISTRATION_STATUS_MAP: dict[int, str] = {
    1: "registered",
}

BMS_GLOBAL_STATUS_MAP: dict[int, str] = {
    3: "synchronized",
}

CHARGE_SOURCE_PRIORITY_MAP: dict[int, str] = {
    3: "solar_first",
}

SMART_PORT_STATUS_MAP: dict[int, str] = {
    0: "off_or_standby",
}

SYSTEM_POWER_STATUS_MAP: dict[int, str] = {
    0: "normal",
}


def normalize_telemetry(
    raw_data: RawPollData,
    *,
    host: str | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    """Normalize raw inverter payloads into Home Assistant friendly telemetry."""
    real_objects = _response_objects(raw_data, "real")
    basic_objects = _response_objects(raw_data, "basic")
    settings_objects = _response_objects(raw_data, "set")

    inverter_real = _merge_inverter_objects(real_objects)
    inverter_serial = _coerce_string(inverter_real.get("DevSN"))

    inverter_basic = _merge_inverter_objects(basic_objects, inverter_serial=inverter_serial)
    if inverter_serial is None:
        inverter_serial = _coerce_string(inverter_basic.get("DevSN"))
        inverter_real = _merge_inverter_objects(real_objects, inverter_serial=inverter_serial)

    inverter_settings = _merge_inverter_objects(
        settings_objects,
        inverter_serial=inverter_serial,
    )

    inverter: dict[str, Any] = {}
    inverter.update(inverter_settings)
    inverter.update(inverter_basic)
    inverter.update(inverter_real)

    bms_objects = (
        _collect_bms_objects(real_objects, inverter_serial=inverter_serial)
        + _collect_bms_objects(basic_objects, inverter_serial=inverter_serial)
    )
    bms = merge_json_objects(bms_objects)

    pv_metrics = _extract_pv_metrics(inverter.get("PV"))
    grid_metrics = _extract_ac_metrics(inverter.get("ACin"))
    load_metrics = _extract_ac_metrics(inverter.get("ACout"))
    generator_metrics = _extract_ac_metrics(inverter.get("GEN"))
    smart_load_metrics = _extract_ac_metrics(inverter.get("SmartL"))
    energy_metrics = _extract_energy_metrics(inverter.get("Energy"))

    battery_voltage_raw = _first_number(
        _nested(inverter, "Batt", 0, 0),
        _nested(bms, "BattList", 0, 0),
    )
    battery_current_raw = _first_number(
        _nested(inverter, "Batt", 1, 0),
        _nested(bms, "BattList", 1, 0),
    )
    battery_power_raw = _number(_nested(inverter, "Batt", 2, 0))

    battery_voltage = _scaled_number(battery_voltage_raw, 0.001, 2)
    battery_current = _scaled_number(battery_current_raw, 0.1, 1)
    battery_power = _round_number(battery_power_raw, 0)

    battery_charge_power: float | int | None = None
    battery_discharge_power: float | int | None = None
    battery_charge_current: float | int | None = None
    battery_discharge_current: float | int | None = None
    if battery_power is not None:
        if battery_power > 0:
            battery_discharge_power = 0
            battery_charge_power = battery_power
            battery_discharge_current = 0
            battery_charge_current = abs(float(battery_current)) if battery_current is not None else 0
        elif battery_power < 0:
            battery_discharge_power = _round_number(abs(float(battery_power)), 0)
            battery_charge_power = 0
            battery_discharge_current = abs(float(battery_current)) if battery_current is not None else 0
            battery_charge_current = 0
        else:
            battery_charge_power = 0
            battery_discharge_power = 0
            battery_charge_current = 0
            battery_discharge_current = 0

    battery_soc = _scaled_number(
        _first_number(
            _nested(inverter, "Batsoc", 0, 0),
            _nested(bms, "BatsocList", 0, 0),
        ),
        0.01,
        1,
    )

    inverter_soh_raw = _number(_nested(inverter, "Batsoc", 0, 1))
    if inverter_soh_raw is not None and inverter_soh_raw > 0:
        battery_state_of_health = _round_number(inverter_soh_raw, 1)
    else:
        battery_state_of_health = _scaled_number(_nested(bms, "BatsocList", 0, 1), 0.1, 1)

    battery_capacity = _scaled_number(_nested(bms, "BatsocList", 0, 2), 0.001, 3)

    transformer_temperature = _scaled_number(_nested(inverter, "Temp", 0, 0), 0.1, 1)
    heatsink_temperature = _scaled_number(_nested(inverter, "Temp", 0, 1), 0.1, 1)
    ambient_temperature = _scaled_number(_nested(inverter, "Temp", 0, 2), 0.1, 1)
    battery_temperature = _normalize_temperature(inverter.get("BatTem"))

    grid_power = grid_metrics["power"]
    grid_import_power = None if grid_power is None else _round_number(max(float(grid_power), 0.0), 0)
    grid_export_power = None if grid_power is None else _round_number(max(-float(grid_power), 0.0), 0)

    pv_power = _positive_value(pv_metrics["total_power"])
    load_power = _positive_value(load_metrics["power"])
    battery_charge = _positive_value(battery_charge_power)
    battery_discharge = _positive_value(battery_discharge_power)

    pv_to_load = _clamp_non_negative(min(pv_power, load_power))
    pv_to_battery = 0.0
    if battery_charge > 0:
        pv_to_battery = _clamp_non_negative(min(max(pv_power - pv_to_load, 0.0), battery_charge))
    pv_to_grid = _clamp_non_negative(max(pv_power - pv_to_load - pv_to_battery, 0.0))

    load_remaining = _clamp_non_negative(load_power - pv_to_load)
    battery_to_load = _clamp_non_negative(min(battery_discharge, load_remaining))
    grid_to_load = _clamp_non_negative(load_remaining - battery_to_load)

    self_consumption_percent = 0.0
    if pv_power > 0:
        self_consumption_percent = _round_number(
            ((pv_to_load + pv_to_battery) / pv_power) * 100.0,
            1,
        )

    battery_roundtrip_efficiency = 0.0
    if battery_charge > 0:
        battery_roundtrip_efficiency = _round_number(
            (battery_discharge / battery_charge) * 100.0,
            1,
        )

    normalized: dict[str, Any] = {
        "communication_protocol_version": _integer(inverter.get("CommVer") or inverter_basic.get("CommVer")),
        "device_serial": _coerce_string(inverter.get("DevSN")) or inverter_serial,
        "wifi_serial": _coerce_string(inverter.get("wifiSN") or inverter_basic.get("wifiSN")),
        "firmware_version": _coerce_string(inverter.get("version") or inverter_basic.get("version")),
        "device_software_version": _coerce_string(inverter.get("DSwVer") or inverter_basic.get("DSwVer")),
        "device_hardware_version": _coerce_string(inverter.get("DHwVer") or inverter_basic.get("DHwVer")),
        "device_type": inverter.get("Type") or inverter_basic.get("Type"),
        "device_subtype": inverter.get("SubType") or inverter_basic.get("SubType"),
        "last_update": _coerce_string(inverter.get("date")),
        "bms_firmware_version": _coerce_string(bms.get("version")),
        "bms_device_serial": _coerce_string(bms.get("DevSN")),
        "bms_inverter_serial": _coerce_string(bms.get("InvSN")),
        "bms_modbus_address": _integer(bms.get("ModAddr")),
        "bms_last_update": _coerce_string(bms.get("date")),
        "load_percent": _scaled_number(inverter.get("lPerc"), 0.1, 1),
        "bus_voltage": _scaled_number(inverter.get("busVp"), 0.1, 1),
        "bus_negative_voltage": _scaled_number(inverter.get("busVn"), 0.1, 1),
        "battery_soc": battery_soc,
        "battery_state_of_health": battery_state_of_health,
        "battery_capacity": battery_capacity,
        "battery_voltage": battery_voltage,
        "battery_current": battery_current,
        "battery_power": battery_power,
        "battery_charge_power": battery_charge_power,
        "battery_discharge_power": battery_discharge_power,
        "battery_charge_current": _round_number(battery_charge_current, 1),
        "battery_discharge_current": _round_number(battery_discharge_current, 1),
        "battery_temperature": battery_temperature,
        "battery_charge_status": _map_enum(inverter.get("bCStat"), BATTERY_CHARGE_STATUS_MAP),
        "pv_voltage": pv_metrics["voltage"],
        "pv_current": pv_metrics["current"],
        "pv_power": pv_metrics["total_power"],
        "pv_total_power": pv_metrics["total_power"],
        "pv1_voltage": pv_metrics["pv1_voltage"],
        "pv1_current": pv_metrics["pv1_current"],
        "pv1_power": pv_metrics["pv1_power"],
        "pv2_voltage": pv_metrics["pv2_voltage"],
        "pv2_current": pv_metrics["pv2_current"],
        "pv2_power": pv_metrics["pv2_power"],
        "pv3_voltage": pv_metrics["pv3_voltage"],
        "pv3_current": pv_metrics["pv3_current"],
        "pv3_power": pv_metrics["pv3_power"],
        "grid_voltage": grid_metrics["voltage"],
        "grid_current": grid_metrics["current"],
        "grid_frequency": grid_metrics["frequency"],
        "grid_power": grid_power,
        "grid_import_power": grid_import_power,
        "grid_export_power": grid_export_power,
        "grid_apparent_power": grid_metrics["apparent_power"],
        "grid_total_power": grid_metrics["total_power"],
        "load_voltage": load_metrics["voltage"],
        "load_current": load_metrics["current"],
        "output_frequency": load_metrics["frequency"],
        "load_power": load_metrics["power"],
        "load_apparent_power": load_metrics["apparent_power"],
        "load_total_power": load_metrics["total_power"],
        "generator_voltage": generator_metrics["voltage"],
        "generator_current": generator_metrics["current"],
        "generator_frequency": generator_metrics["frequency"],
        "generator_power": generator_metrics["power"],
        "generator_apparent_power": generator_metrics["apparent_power"],
        "generator_total_power": generator_metrics["total_power"],
        "smart_load_voltage": smart_load_metrics["voltage"],
        "smart_load_current": smart_load_metrics["current"],
        "smart_load_frequency": smart_load_metrics["frequency"],
        "smart_load_power": smart_load_metrics["power"],
        "smart_load_apparent_power": smart_load_metrics["apparent_power"],
        "smart_load_total_power": smart_load_metrics["total_power"],
        "transformer_temperature": transformer_temperature,
        "heatsink_temperature": heatsink_temperature,
        "ambient_temperature": ambient_temperature,
        "inverter_temperature": transformer_temperature,
        "inverter_mode": _map_mode(inverter.get("workM")),
        "inverter_warning_code": inverter.get("warn"),
        "inverter_fault_code": inverter.get("fault"),
        "power_flow_status_raw": _integer(inverter.get("pFlow")),
        "power_flow_secondary_status_raw": _integer(inverter.get("pFlowE1")),
        "pv_to_load_power": _round_number(pv_to_load, 0),
        "pv_to_battery_power": _round_number(pv_to_battery, 0),
        "pv_to_grid_power": _round_number(pv_to_grid, 0),
        "battery_to_load_power": _round_number(battery_to_load, 0),
        "grid_to_load_power": _round_number(grid_to_load, 0),
        "self_consumption_percent": self_consumption_percent,
        "battery_roundtrip_efficiency": battery_roundtrip_efficiency,
        **energy_metrics,
        "bms_count": _integer(inverter.get("bmsNum")),
        "wifi_status": _map_enum(inverter.get("setWifi"), WIFI_STATUS_MAP),
        "bms_communication_status": _map_enum(inverter.get("BMSFlE"), BMS_COMMUNICATION_STATUS_MAP),
        "bms_registration_status": _map_enum(inverter.get("BMSFlg"), BMS_REGISTRATION_STATUS_MAP),
        "bms_global_status": _map_enum(inverter.get("BFlgAll"), BMS_GLOBAL_STATUS_MAP),
        "charge_source_priority": _map_enum(inverter.get("cSPri"), CHARGE_SOURCE_PRIORITY_MAP),
        "max_ac_charge_current_limit": _round_number(inverter.get("MACCurr"), 0),
        "smart_port_status": _map_enum(inverter.get("SmartS"), SMART_PORT_STATUS_MAP),
        "system_power_status": _map_enum(inverter.get("SPStus"), SYSTEM_POWER_STATUS_MAP),
        "bms_fault_code": _integer(bms.get("BBfault")),
        "bms_warning_code": _integer(bms.get("BBwarn")),
        "bms_state": _integer(bms.get("Bstate")),
        "bms_pack_voltage": _scaled_number(_nested(bms, "BattList", 0, 0), 0.001, 2),
        "bms_pack_current": _scaled_number(_nested(bms, "BattList", 1, 0), 0.1, 1),
        "bms_pack_soc": _scaled_number(_nested(bms, "BatsocList", 0, 0), 0.01, 1),
        "bms_pack_state_of_health": _scaled_number(_nested(bms, "BatsocList", 0, 1), 0.1, 1),
        "bms_total_capacity": _scaled_number(_nested(bms, "BatsocList", 0, 2), 0.001, 3),
        "bms_max_cell_voltage": _scaled_number(_nested(bms, "BMaxMin", 0, 0), 0.001, 3),
        "bms_min_cell_voltage": _scaled_number(_nested(bms, "BMaxMin", 0, 1), 0.001, 3),
        "bms_max_cell_temperature": _round_number(_nested(bms, "BMaxMin", 1, 0), 1),
        "bms_min_cell_temperature": _round_number(_nested(bms, "BMaxMin", 1, 1), 1),
        "bms_parallel_count": _integer(_nested(bms, "BMSpara", 0, 0)),
        "bms_hardware_config": _integer(_nested(bms, "BMSpara", 0, 1)),
        "bms_charge_voltage_limit": _scaled_number(_nested(bms, "BLVolCu", 0, 0), 0.1, 1),
        "bms_discharge_voltage_limit": _scaled_number(_nested(bms, "BLVolCu", 0, 1), 0.1, 1),
        "bms_charge_current_limit": _scaled_number(_nested(bms, "BLVolCu", 1, 0), 0.1, 1),
        "bms_discharge_current_limit": _scaled_number(_nested(bms, "BLVolCu", 1, 1), 0.1, 1),
        "bms_temperature_1": _normalize_temperature(_nested(bms, "Templist", 0, 0)),
        "bms_temperature_2": _normalize_temperature(_nested(bms, "Templist", 0, 1)),
        "raw_json_payload": _coerce_string(inverter.get("date")) or "available",
        "_raw_payloads": {
            key: response.raw
            for key, response in raw_data.responses.items()
            if response.raw is not None
        },
        "_raw_objects": {
            key: response.objects
            for key, response in raw_data.responses.items()
        },
        "_raw_inverter": inverter,
        "_raw_bms": bms,
        "_raw_settings": inverter_settings,
        "_raw_energy_counters": inverter.get("Energy"),
        "_ac_layouts": {
            "grid": grid_metrics["layout"],
            "load": load_metrics["layout"],
            "generator": generator_metrics["layout"],
            "smart_load": smart_load_metrics["layout"],
            "pv": pv_metrics["layout"],
        },
    }

    if host is not None:
        normalized["host"] = host
    if port is not None:
        normalized["port"] = port

    return normalized


def _response_objects(raw_data: RawPollData, key: str) -> list[dict[str, Any]]:
    response = raw_data.responses.get(key)
    if response is None:
        return []
    return [obj for obj in response.objects if isinstance(obj, dict)]


def _merge_inverter_objects(
    objects: list[dict[str, Any]],
    inverter_serial: str | None = None,
) -> dict[str, Any]:
    primary = _select_primary_inverter_object(objects, inverter_serial=inverter_serial)
    if not primary:
        return {}

    serial = inverter_serial or _coerce_string(primary.get("DevSN"))
    merged: dict[str, Any] = {}
    for obj in objects:
        if _belongs_to_primary_inverter(obj, serial):
            merged.update(obj)

    if not merged:
        merged.update(primary)
    return merged


def _select_primary_inverter_object(
    objects: list[dict[str, Any]],
    inverter_serial: str | None = None,
) -> dict[str, Any]:
    if inverter_serial is not None:
        for obj in objects:
            if _belongs_to_primary_inverter(obj, inverter_serial):
                return obj

    for obj in objects:
        if obj.get("Type") == INVERTER_TYPE:
            return obj

    for obj in objects:
        if obj.get("Type") != BMS_TYPE:
            return obj

    return objects[0] if objects else {}


def _belongs_to_primary_inverter(obj: dict[str, Any], inverter_serial: str | None) -> bool:
    obj_type = obj.get("Type")
    if obj_type == BMS_TYPE:
        return False

    if inverter_serial and obj.get("DevSN") == inverter_serial:
        return True

    if obj_type == INVERTER_TYPE:
        return True

    return inverter_serial is None and obj_type is None


def _collect_bms_objects(
    objects: list[dict[str, Any]],
    *,
    inverter_serial: str | None,
) -> list[dict[str, Any]]:
    return [obj for obj in objects if _is_bms_object(obj, inverter_serial)]


def _is_bms_object(obj: dict[str, Any], inverter_serial: str | None) -> bool:
    if obj.get("Type") == BMS_TYPE:
        return True

    if inverter_serial is None:
        return False

    return obj.get("InvSN") == inverter_serial and obj.get("DevSN") != inverter_serial


def _extract_pv_metrics(block: Any) -> dict[str, Any]:
    if _pv_is_row_aggregated(block):
        voltage = _scaled_number(_nested(block, 0, 0), 0.1, 1)
        current = _scaled_number(_nested(block, 1, 0), 0.1, 1)
        power = _round_number(_nested(block, 2, 0), 0)
        total_power = _round_number(
            _first_non_zero_number(_nested(block, 3, 0), _nested(block, 2, 0)),
            0,
        )
        return {
            "layout": "row_aggregated",
            "voltage": voltage,
            "current": current,
            "power": power,
            "total_power": total_power if total_power is not None else power,
            "pv1_voltage": voltage,
            "pv1_current": current,
            "pv1_power": power,
            "pv2_voltage": None,
            "pv2_current": None,
            "pv2_power": None,
            "pv3_voltage": None,
            "pv3_current": None,
            "pv3_power": None,
        }

    pv1_voltage = _scaled_number(_nested(block, 0, 0), 0.1, 1)
    pv1_current = _scaled_number(_nested(block, 0, 1), 0.1, 1)
    pv1_power = _round_number(_nested(block, 0, 2), 0)

    pv2_voltage = _scaled_number(_nested(block, 1, 0), 0.1, 1)
    pv2_current = _scaled_number(_nested(block, 1, 1), 0.1, 1)
    pv2_power = _round_number(_nested(block, 1, 2), 0)

    pv3_voltage = _scaled_number(_nested(block, 2, 0), 0.1, 1)
    pv3_current = _scaled_number(_nested(block, 2, 1), 0.1, 1)
    pv3_power = _round_number(_nested(block, 2, 2), 0)

    total_power = _round_number(_nested(block, 3, 0), 0)

    aggregated_layout = _pv_is_aggregated(block)
    if aggregated_layout:
        pv1_voltage = _scaled_number(_nested(block, 0, 0), 0.1, 1)
        pv1_current = _scaled_number(_nested(block, 1, 0), 0.1, 1)
        pv1_power = _round_number(
            _first_non_zero_number(_nested(block, 2, 0), _nested(block, 3, 0)),
            0,
        )
        total_power = _round_number(
            _first_non_zero_number(_nested(block, 3, 0), _nested(block, 2, 0)),
            0,
        )
        return {
            "layout": "aggregated",
            "voltage": pv1_voltage,
            "current": pv1_current,
            "power": pv1_power,
            "total_power": total_power if total_power is not None else pv1_power,
            "pv1_voltage": pv1_voltage,
            "pv1_current": pv1_current,
            "pv1_power": pv1_power,
            "pv2_voltage": None,
            "pv2_current": None,
            "pv2_power": None,
            "pv3_voltage": None,
            "pv3_current": None,
            "pv3_power": None,
        }

    total_current = _sum_numbers(pv1_current, pv2_current, pv3_current)
    if total_power is None:
        total_power = _round_number(_sum_numbers(pv1_power, pv2_power, pv3_power), 0)

    return {
        "layout": "legacy",
        "voltage": pv1_voltage,
        "current": total_current,
        "power": total_power,
        "total_power": total_power,
        "pv1_voltage": pv1_voltage,
        "pv1_current": pv1_current,
        "pv1_power": pv1_power,
        "pv2_voltage": pv2_voltage,
        "pv2_current": pv2_current,
        "pv2_power": pv2_power,
        "pv3_voltage": pv3_voltage,
        "pv3_current": pv3_current,
        "pv3_power": pv3_power,
    }


def _pv_is_aggregated(block: Any) -> bool:
    voltage = _number(_nested(block, 0, 0))
    string1_current = _number(_nested(block, 0, 1))
    string1_power = _number(_nested(block, 0, 2))
    aggregate_current = _number(_nested(block, 1, 0))
    aggregate_power = _number(_nested(block, 2, 0))

    if voltage is None or voltage <= 500:
        return False
    if string1_current not in (None, 0):
        return False
    if string1_power not in (None, 0):
        return False
    if aggregate_current is None and aggregate_power is None:
        return False
    return True


def _pv_is_row_aggregated(block: Any) -> bool:
    voltage = _number(_nested(block, 0, 0))
    current = _number(_nested(block, 1, 0))
    power = _number(_nested(block, 2, 0))

    if voltage is None or current is None or power is None:
        return False

    if _number(_nested(block, 0, 1)) not in (None, 0):
        return False
    if _number(_nested(block, 0, 2)) not in (None, 0):
        return False
    if _number(_nested(block, 1, 1)) not in (None, 0):
        return False
    if _number(_nested(block, 1, 2)) not in (None, 0):
        return False
    if _number(_nested(block, 2, 1)) not in (None, 0):
        return False
    if _number(_nested(block, 2, 2)) not in (None, 0):
        return False

    return voltage > 0 and current >= 0 and power >= 0


def _extract_ac_metrics(block: Any) -> dict[str, Any]:
    voltage = _scaled_number(_nested(block, 0, 0), 0.1, 1)
    current = _scaled_number(_nested(block, 1, 0), 0.1, 1)

    slot2 = _number(_nested(block, 2, 0))
    slot3_primary = _number(_nested(block, 3, 0))
    slot3_secondary = _number(_nested(block, 3, 1))
    slot4 = _number(_nested(block, 4, 0))

    expected_apparent = None
    if voltage is not None and current is not None:
        expected_apparent = float(voltage) * float(current)

    slot2_frequency = _candidate_frequency(slot2)
    slot3_frequency = _candidate_frequency(slot3_primary)
    slot4_frequency = _candidate_frequency(slot4)

    use_frequency_layout = False
    if slot2_frequency is not None:
        score = 0
        if slot3_secondary is not None and expected_apparent is not None:
            tolerance = max(50.0, expected_apparent * 0.35)
            if abs(slot3_secondary - expected_apparent) <= tolerance:
                score += 2
            score += 1
        if slot4 is not None and slot4 >= 0:
            score += 1
        use_frequency_layout = score >= 1

    layout = "power_index_2"
    frequency = None
    active_power = None
    apparent_power = None
    total_power = None

    if use_frequency_layout:
        layout = "frequency_index_2"
        frequency = slot2_frequency
        active_power = slot3_primary
        apparent_power = slot3_secondary
        total_power = slot4 if slot4 not in (None, 0) else slot3_primary
    else:
        active_power = slot2 if slot2 is not None else slot3_primary
        frequency = slot3_frequency or slot4_frequency
        apparent_power = slot3_secondary
        total_power = slot4 if slot4 not in (None, 0) else active_power

    return {
        "layout": layout,
        "voltage": voltage,
        "current": current,
        "frequency": frequency,
        "power": _round_number(active_power, 0),
        "apparent_power": _round_number(apparent_power, 0),
        "total_power": _round_number(total_power, 0),
    }


def _extract_energy_metrics(block: Any) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for prefix, row_index, period_indexes in (
        ("pv_yield_energy", 0, {"total": 1, "daily": 2, "monthly": 3, "yearly": 4}),
        ("load_consumption_energy", 1, {"total": 1, "daily": 2, "monthly": 3, "yearly": 4}),
        ("grid_export_energy", 2, {"daily": 1, "monthly": 2, "yearly": 3, "total": 4}),
        ("grid_import_energy", 3, {"daily": 1, "monthly": 2, "yearly": 3, "total": 4}),
        ("battery_charge_energy", 4, {"daily": 1, "monthly": 2, "yearly": 3, "total": 4}),
        ("battery_discharge_energy", 5, {"daily": 1, "monthly": 2, "yearly": 3, "total": 4}),
    ):
        for period, index in period_indexes.items():
            metrics[f"{prefix}_{period}"] = _scaled_number(
                _nested(block, row_index, index),
                0.001,
                3,
            )
    return metrics


def _candidate_frequency(value: float | int | None) -> float | None:
    if value is None:
        return None

    raw = float(value)
    for divisor in (100.0, 10.0, 1.0):
        candidate = raw / divisor
        if 40.0 < candidate < 70.0:
            return round(candidate, 2)
    return None


def _map_mode(value: Any) -> str | None:
    mode = _integer(value)
    if mode is None:
        return None
    return MODE_MAP.get(mode, f"unknown ({mode})")


def _map_enum(value: Any, mapping: dict[int, str]) -> str | None:
    raw = _integer(value)
    if raw is None:
        return None
    return mapping.get(raw, str(raw))


def _normalize_temperature(value: Any) -> float | None:
    raw = _number(value)
    if raw is None:
        return None

    candidate = raw / 10.0 if abs(raw) > 100 else raw
    if -40.0 <= candidate <= 120.0:
        return round(candidate, 1)
    return None


def _nested(value: Any, *path: Any) -> Any:
    current = value
    try:
        for part in path:
            current = current[part]
    except (KeyError, IndexError, TypeError):
        return None
    return current


def _first_number(*values: Any) -> float | int | None:
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return value
    return None


def _first_non_zero_number(*values: Any) -> float | int | None:
    zero_candidate: float | int | None = None
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            if float(value) != 0.0:
                return value
            if zero_candidate is None:
                zero_candidate = value
    return zero_candidate


def _sum_numbers(*values: Any) -> float | None:
    numbers = [float(value) for value in values if isinstance(value, (int, float))]
    if not numbers:
        return None
    return sum(numbers)


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _scaled_number(value: Any, factor: float, digits: int) -> float | None:
    raw = _number(value)
    if raw is None:
        return None
    return round(raw * factor, digits)


def _round_number(value: Any, digits: int) -> float | int | None:
    raw = _number(value)
    if raw is None:
        return None
    if digits == 0:
        return int(round(raw))
    return round(raw, digits)


def _positive_value(value: Any) -> float:
    raw = _number(value)
    if raw is None:
        return 0.0
    return max(raw, 0.0)


def _clamp_non_negative(value: float) -> float:
    return max(value, 0.0)


def _coerce_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
