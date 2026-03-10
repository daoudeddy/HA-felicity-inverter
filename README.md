# Felicity Inverter

Custom Home Assistant integration for Felicity inverter WiFi telemetry over the local TCP interface on port `53970`.

The integration polls these commands:

- `wifilocalMonitor:get dev real infor`
- `wifilocalMonitor:get dev basice infor`
- `wifilocalMonitor:get dev set infor`

The inverter may return multiple JSON objects concatenated together with no separators. The integration now splits and parses those payloads safely, keeps the inverter packet (`Type: 80`) as the primary device identity, and preserves BMS packets (`Type: 112`) separately for battery diagnostics.

## Features

- Config flow with **IP**, **port**, and **scan interval**
- Default polling interval: **5 seconds**
- TCP polling with automatic retry on the next cycle if a request fails
- Clean normalized telemetry for Home Assistant sensors
- CSV-aligned runtime mapping for inverter and BMS payloads
- Power-flow sensors for dashboards and automations
- Energy Dashboard compatible power sensors
- PV string sensors and expanded AC-side metrics
- BMS summary and limit diagnostics
- Diagnostic device metadata sensors
- Optional raw JSON diagnostic sensor disabled by default

## Installation

### HACS

1. Open **HACS → Integrations → Custom repositories**
2. Add `https://github.com/vitalik33-tir/HA-felicity-inverter`
3. Select **Integration**
4. Install the repository and restart Home Assistant
5. Add **Felicity Inverter** from **Settings → Devices & services**

### Manual

Copy `custom_components/felicity_inverter` into your Home Assistant `config/custom_components/` directory and restart Home Assistant.

## Configuration

Add the integration from the UI and configure:

- **Name**
- **Host / IP**
- **Port** (default: `53970`)
- **Scan interval** in seconds (default: `5`)

Host, port, and scan interval can also be changed later in the integration options.

## Sensor groups

The integration exposes normalized sensors in these groups:

- **Battery**
  - SOC, voltage, current, signed power
  - charge / discharge power
  - charge / discharge current
  - battery temperature
- **PV**
  - total voltage, current, power
  - PV1 / PV2 / PV3 voltage, current, power when exposed by the inverter
- **Grid**
  - voltage, current, frequency
  - active power, apparent power, total power
  - import power, export power
- **Load**
  - voltage, current, frequency
  - active power, apparent power, total power
- **Generator**
  - voltage, current, frequency
  - active power, apparent power, total power
- **Smart Load**
  - voltage, current, frequency
  - active power, apparent power, total power
- **Energy Flow**
  - PV → Load
  - PV → Battery
  - PV → Grid
  - Battery → Load
  - Grid → Load
  - self consumption
  - battery roundtrip efficiency
- **System**
  - inverter mode
  - bus voltage
  - bus negative voltage
  - load percent
- **Temperature**
  - inverter temperature
  - transformer temperature
  - heatsink temperature
  - ambient temperature
  - battery temperature
- **Diagnostic Energy Counters**
  - daily / monthly / yearly / total PV yield
  - daily / monthly / yearly / total load consumption
  - daily / monthly / yearly / total grid import / export
  - daily / monthly / yearly / total battery charge / discharge
- **Warnings / Faults**
  - warning code
  - fault code
  - matching binary sensors
- **BMS Diagnostics**
  - BMS firmware, serial, inverter serial, and Modbus address
  - pack voltage, current, SOC, SOH, capacity
  - charge / discharge voltage limits
  - charge / discharge current limits
  - max / min cell voltage and temperature summary values
  - communication, registration, and global status values
- **Diagnostics**
  - device serial
  - WiFi serial
  - firmware version
  - device software version
  - device hardware version
  - raw JSON payload sensor (disabled by default)

## Energy Dashboard

This integration exposes real-time power sensors for:

- `pv_power`
- `grid_import_power`
- `grid_export_power`
- `load_power`
- `battery_charge_power`
- `battery_discharge_power`

Use Home Assistant statistics/helpers to derive energy from those power sensors. The integration does **not** manually integrate energy in software.

The inverter `Energy[][]` counters are exposed as diagnostic sensors for reference, including PV yield, load consumption, grid import/export, and battery charge/discharge totals.

`pFlow` is treated as a raw UI power-flow status bitmask, not as an energy counter.

## Debug logging

```yaml
logger:
  default: info
  logs:
    custom_components.felicity_inverter: debug
```

## Notes

- If TCP communication fails, entities become unavailable until the next successful poll.
- The integration supports multiple AC payload layouts and automatically normalizes them into one sensor model.
- The raw JSON sensor is diagnostic only and disabled by default to avoid unnecessary state growth.
