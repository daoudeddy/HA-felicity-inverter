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

    battery_soc_raw = _first_number(
        _nested(inverter, "Batsoc", 0, 0),
        _nested(bms, "BatsocList", 0, 0),
    )
    battery_soc = _scaled_number(battery_soc_raw, 0.01, 1)

    inverter_temperature = _scaled_number(_nested(inverter, "Temp", 0, 0), 0.1, 1)
    battery_temperature = _normalize_temperature(
        _first_number(
            inverter.get("BatTem"),
            _nested(bms, "Templist", 0, 0),
        )
    )

    grid_power = grid_metrics["power"]
    grid_import_power = None if grid_power is None else _round_number(max(float(grid_power), 0.0), 0)
    grid_export_power = None if grid_power is None else _round_number(max(-float(grid_power), 0.0), 0)

    pv_power = _positive_value(pv_metrics["power"])
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
        "device_serial": _coerce_string(inverter.get("DevSN")) or inverter_serial,
        "wifi_serial": _coerce_string(inverter.get("wifiSN") or inverter_basic.get("wifiSN")),
        "firmware_version": _coerce_string(inverter.get("version") or inverter_basic.get("version")),
        "device_software_version": _coerce_string(inverter.get("DSwVer") or inverter_basic.get("DSwVer")),
        "device_hardware_version": _coerce_string(inverter.get("DHwVer") or inverter_basic.get("DHwVer")),
        "device_type": inverter.get("Type") or inverter_basic.get("Type"),
        "device_subtype": inverter.get("SubType") or inverter_basic.get("SubType"),
        "last_update": _coerce_string(inverter.get("date")),
        "load_percent": _scaled_number(inverter.get("lPerc"), 0.1, 1),
        "bus_voltage": _scaled_number(inverter.get("busVp"), 0.01, 2),
        "battery_soc": battery_soc,
        "battery_voltage": battery_voltage,
        "battery_current": battery_current,
        "battery_power": battery_power,
        "battery_charge_power": battery_charge_power,
        "battery_discharge_power": battery_discharge_power,
        "battery_charge_current": _round_number(battery_charge_current, 1),
        "battery_discharge_current": _round_number(battery_discharge_current, 1),
        "battery_temperature": battery_temperature,
        "pv_voltage": pv_metrics["voltage"],
        "pv_current": pv_metrics["current"],
        "pv_power": pv_metrics["power"],
        "grid_voltage": grid_metrics["voltage"],
        "grid_current": grid_metrics["current"],
        "grid_frequency": grid_metrics["frequency"],
        "grid_import_power": grid_import_power,
        "grid_export_power": grid_export_power,
        "load_voltage": load_metrics["voltage"],
        "load_current": load_metrics["current"],
        "output_frequency": load_metrics["frequency"],
        "load_power": load_metrics["power"],
        "generator_voltage": generator_metrics["voltage"],
        "generator_current": generator_metrics["current"],
        "generator_power": generator_metrics["power"],
        "smart_load_voltage": smart_load_metrics["voltage"],
        "smart_load_current": smart_load_metrics["current"],
        "smart_load_power": smart_load_metrics["power"],
        "inverter_temperature": inverter_temperature,
        "inverter_mode": _map_mode(inverter.get("workM")),
        "inverter_warning_code": inverter.get("warn"),
        "inverter_fault_code": inverter.get("fault"),
        "inverter_throughput_energy": _scaled_number(inverter.get("pFlow"), 0.001, 3),
        "pv_to_load_power": _round_number(pv_to_load, 0),
        "pv_to_battery_power": _round_number(pv_to_battery, 0),
        "pv_to_grid_power": _round_number(pv_to_grid, 0),
        "battery_to_load_power": _round_number(battery_to_load, 0),
        "grid_to_load_power": _round_number(grid_to_load, 0),
        "self_consumption_percent": self_consumption_percent,
        "battery_roundtrip_efficiency": battery_roundtrip_efficiency,
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

    _populate_cell_telemetry(normalized, bms)
    return normalized


def _populate_cell_telemetry(target: dict[str, Any], bms: dict[str, Any]) -> None:
    cell_values = _nested(bms, "BatcelList", 0)
    for index in range(16):
        key = f"battery_cell_{index + 1}_voltage"
        raw_value = _nested(cell_values, index)
        if raw_value in (None, 0):
            target[key] = None
            continue
        target[key] = _scaled_number(raw_value, 0.001, 3)

    temperature_values = _nested(bms, "BtemList", 0)
    for index in range(8):
        key = f"battery_cell_{index + 1}_temperature"
        raw_value = _nested(temperature_values, index)
        if raw_value in (None, 0):
            target[key] = None
            continue
        target[key] = _normalize_temperature(raw_value)


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
    voltage = _scaled_number(_nested(block, 0, 0), 0.1, 1)
    aggregated_current = _number(_nested(block, 1, 0))
    aggregated_power = _number(_nested(block, 2, 0))

    legacy_currents = [_number(_nested(block, index, 1)) for index in range(3)]
    legacy_powers = [_number(_nested(block, index, 2)) for index in range(3)]
    total_power = _number(_nested(block, 3, 0))

    use_aggregated_layout = (
        aggregated_current is not None
        and all(value in (None, 0) for value in legacy_currents)
        and all(value in (None, 0) for value in legacy_powers)
    )

    if use_aggregated_layout:
        return {
            "layout": "aggregated",
            "voltage": voltage,
            "current": _scaled_number(aggregated_current, 0.1, 1),
            "power": _round_number(_first_number(aggregated_power, total_power), 0),
        }

    current_values = [value for value in legacy_currents if value is not None]
    current = None
    if current_values:
        current = _round_number(sum(value / 10.0 for value in current_values), 1)
    elif aggregated_current is not None:
        current = _scaled_number(aggregated_current, 0.1, 1)

    power_value = total_power
    if power_value is None:
        power_candidates = [value for value in legacy_powers if value is not None]
        if power_candidates:
            power_value = sum(power_candidates)
        else:
            power_value = aggregated_power

    return {
        "layout": "legacy",
        "voltage": voltage,
        "current": current,
        "power": _round_number(power_value, 0),
    }


def _extract_ac_metrics(block: Any) -> dict[str, Any]:
    voltage = _scaled_number(_nested(block, 0, 0), 0.1, 1)
    current = _scaled_number(_nested(block, 1, 0), 0.1, 1)

    slot2 = _number(_nested(block, 2, 0))
    slot3_power = _number(_nested(block, 3, 0))
    slot3_apparent = _number(_nested(block, 3, 1))
    slot4 = _number(_nested(block, 4, 0))

    expected_apparent = None
    if voltage is not None and current is not None:
        expected_apparent = float(voltage) * float(current)

    slot2_frequency = _candidate_frequency(slot2)
    slot3_frequency = _candidate_frequency(slot3_power)
    slot4_frequency = _candidate_frequency(slot4)

    use_frequency_layout = False
    if slot2_frequency is not None:
        score = 0
        if slot3_apparent is not None and expected_apparent is not None:
            tolerance = max(50.0, expected_apparent * 0.35)
            if abs(slot3_apparent - expected_apparent) <= tolerance:
                score += 2
            score += 1

        if (
            slot3_power is not None
            and expected_apparent is not None
            and (expected_apparent > 0 or slot3_apparent is not None)
        ):
            tolerance = max(75.0, expected_apparent * 0.75)
            if abs(abs(slot3_power) - expected_apparent) <= tolerance:
                score += 1

        use_frequency_layout = score >= 1

    frequency = None
    active_power = None
    layout = "power_index_2"

    if use_frequency_layout:
        layout = "frequency_index_2"
        frequency = slot2_frequency
        active_power = slot3_power
        if active_power is None:
            active_power = slot2
    else:
        active_power = slot2 if slot2 is not None else slot3_power
        frequency = slot3_frequency or slot4_frequency

    if active_power is None and slot3_apparent is not None:
        active_power = slot3_apparent

    return {
        "layout": layout,
        "voltage": voltage,
        "current": current,
        "frequency": frequency,
        "power": _round_number(active_power, 0),
    }


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
