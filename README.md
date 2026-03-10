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
- Power-flow sensors for dashboards and automations
- Energy Dashboard compatible power sensors
- Diagnostic device metadata sensors
- BMS cell voltage and cell temperature monitoring
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
  - voltage, current, power
- **Grid**
  - voltage, current, frequency
  - import power, export power
- **Load**
  - voltage, current, frequency, power
- **Generator**
  - voltage, current, power
- **Smart Load**
  - voltage, current, power
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
  - load percent
  - throughput energy
- **Temperature**
  - inverter temperature
  - battery temperature
- **Warnings / Faults**
  - warning code
  - fault code
  - matching binary sensors
- **Diagnostics**
  - device serial
  - WiFi serial
  - firmware version
  - device software version
  - device hardware version
  - raw JSON payload sensor (disabled by default)
- **BMS Cells**
  - up to 16 cell voltage sensors
  - up to 8 cell temperature sensors

## Energy Dashboard

This integration exposes real-time power sensors for:

- `pv_power`
- `grid_import_power`
- `grid_export_power`
- `load_power`
- `battery_charge_power`
- `battery_discharge_power`

Use Home Assistant statistics/helpers to derive energy from those power sensors. The integration does **not** manually integrate energy in software.

The only native energy sensor kept by the integration is:

- `inverter_throughput_energy`

This sensor uses:

- `device_class = energy`
- `state_class = total_increasing`
- `unit = kWh`

and does not use `last_reset`.

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
