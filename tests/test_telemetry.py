from __future__ import annotations

import importlib.util
import unittest

HOMEASSISTANT_AVAILABLE = importlib.util.find_spec("homeassistant") is not None

if HOMEASSISTANT_AVAILABLE:
    from custom_components.felicity_inverter.api import ParsedResponse, RawPollData
    from custom_components.felicity_inverter.telemetry import normalize_telemetry
else:  # pragma: no cover - environment dependent
    ParsedResponse = RawPollData = normalize_telemetry = None


def _sample_poll_data() -> RawPollData:
    real_objects = [
        {
            "CommVer": 1,
            "wifiSN": "I020906004825471655",
            "date": "20260310084150",
            "DevSN": "020906004825471655",
            "Type": 80,
            "SubType": 1035,
            "workM": 3,
            "pFlow": 62689,
            "warn": 0,
            "fault": 0,
            "lPerc": 30,
            "busVp": 4315,
            "BatTem": 15,
            "ACin": [[2224, None, None], [0, None, None], [4941, None, None], [0, 0], [0, None, None]],
            "ACout": [[2304, None, None], [9, None, None], [4941, None, None], [180, 207, 0], [180, None, None]],
            "PV": [[1823, 0, 0], [64, 0, 0], [1176, 0, 0], [0]],
            "Temp": [[380, 300, 340]],
            "Batt": [[55970], [140], [783, 0]],
            "Batsoc": [[9700, 0, 0]],
            "Energy": [
                [0, 1536, 1536, 1536, 1536],
                [0, 2485, 863, 2485, 2485],
                [0, 120, 240, 360, 480],
                [0, 80, 160, 240, 320],
                [0, 50, 100, 150, 200],
                [0, 40, 80, 120, 160],
            ],
            "GEN": [[0, None, None], [0, None, None], [0, None, None], [0, 0], [0, None, None]],
            "SmartL": [[0, None, None], [0, None, None], [0, None, None], [0, 0], [0, None, None]],
        },
        {
            "CommVer": 1,
            "wifiSN": "I020906004825471655",
            "version": "2.13",
            "DevSN": "072604810025520550",
            "InvSN": "020906004825471655",
            "date": "20260310084150",
            "Type": 112,
            "Templist": [[190, 180], [1, 0], [None], [None]],
            "BattList": [[55870, None], [150, None]],
            "BatsocList": [[9700, 1000, 100000]],
            "BatcelList": [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
            "BtemList": [[0, 0, 0, 0, 0, 0, 0, 0]],
        },
    ]
    basic_objects = [
        {
            "CommVer": 1,
            "version": "2.13",
            "wifiSN": "I020906004825471655",
            "DevSN": "020906004825471655",
            "Type": 80,
            "SubType": 1035,
            "DSwVer": 110,
            "DHwVer": 1000,
        },
        {
            "CommVer": 1,
            "wifiSN": "I020906004825471655",
            "version": "2.13",
            "DevSN": "072604810025520550",
            "Type": 112,
            "DSwVer": 65535,
            "DHwVer": 0,
            "InvSN": "020906004825471655",
        },
    ]
    settings_objects = [
        {"CommVer": 1, "DevSN": "020906004825471655", "ttlPack": 2, "index": 1, "Type": 80, "buzEn": 1},
        {"CommVer": 1, "DevSN": "020906004825471655", "ttlPack": 2, "index": 2, "Type": 80, "FltClr": 0},
    ]

    return RawPollData(
        responses={
            "real": ParsedResponse(command="real", raw="real", objects=real_objects),
            "basic": ParsedResponse(command="basic", raw="basic", objects=basic_objects),
            "set": ParsedResponse(command="set", raw="set", objects=settings_objects),
        }
    )


class TelemetryNormalizationTests(unittest.TestCase):
    @unittest.skipUnless(HOMEASSISTANT_AVAILABLE, "homeassistant not installed")
    def test_normalize_telemetry_keeps_inverter_identity(self) -> None:
        data = normalize_telemetry(_sample_poll_data())

        self.assertEqual(data["device_serial"], "020906004825471655")
        self.assertEqual(data["wifi_serial"], "I020906004825471655")
        self.assertEqual(data["firmware_version"], "2.13")
        self.assertEqual(data["device_software_version"], "110")
        self.assertEqual(data["device_hardware_version"], "1000")
        self.assertEqual(data["bms_firmware_version"], "2.13")
        self.assertEqual(data["bms_device_serial"], "072604810025520550")
        self.assertEqual(data["bms_inverter_serial"], "020906004825471655")
        self.assertEqual(data["_raw_bms"]["DevSN"], "072604810025520550")

    @unittest.skipUnless(HOMEASSISTANT_AVAILABLE, "homeassistant not installed")
    def test_normalize_telemetry_extracts_sample_metrics(self) -> None:
        data = normalize_telemetry(_sample_poll_data())

        self.assertEqual(data["battery_voltage"], 55.97)
        self.assertEqual(data["battery_current"], 14.0)
        self.assertEqual(data["battery_power"], 783)
        self.assertEqual(data["battery_charge_power"], 783)
        self.assertEqual(data["battery_discharge_power"], 0)
        self.assertEqual(data["battery_soc"], 97.0)
        self.assertEqual(data["battery_state_of_health"], 100.0)
        self.assertEqual(data["battery_capacity"], 100.0)
        self.assertEqual(data["pv_voltage"], 182.3)
        self.assertEqual(data["pv_current"], 6.4)
        self.assertEqual(data["pv_power"], 1176)
        self.assertEqual(data["pv_total_power"], 1176)
        self.assertEqual(data["pv1_voltage"], 182.3)
        self.assertEqual(data["pv1_current"], 6.4)
        self.assertEqual(data["pv1_power"], 1176)
        self.assertEqual(data["bus_voltage"], 431.5)
        self.assertEqual(data["inverter_mode"], "hybrid")
        self.assertEqual(data["inverter_temperature"], 38.0)
        self.assertEqual(data["transformer_temperature"], 38.0)
        self.assertEqual(data["heatsink_temperature"], 30.0)
        self.assertEqual(data["ambient_temperature"], 34.0)
        self.assertEqual(data["battery_temperature"], 15.0)
        self.assertEqual(data["grid_frequency"], 49.41)
        self.assertEqual(data["output_frequency"], 49.41)
        self.assertEqual(data["load_power"], 180)
        self.assertEqual(data["load_apparent_power"], 207)
        self.assertEqual(data["pv_to_load_power"], 180)
        self.assertEqual(data["pv_to_battery_power"], 783)
        self.assertEqual(data["pv_to_grid_power"], 213)
        self.assertEqual(data["battery_to_load_power"], 0)
        self.assertEqual(data["power_flow_status_raw"], 62689)
        self.assertEqual(data["pv_yield_energy_total"], 1.536)
        self.assertEqual(data["pv_yield_energy_daily"], 1.536)
        self.assertEqual(data["load_consumption_energy_total"], 2.485)
        self.assertEqual(data["load_consumption_energy_daily"], 0.863)
        self.assertEqual(data["load_consumption_energy_monthly"], 2.485)
        self.assertEqual(data["grid_export_energy_total"], 0.48)
        self.assertEqual(data["grid_import_energy_total"], 0.32)
        self.assertEqual(data["battery_charge_energy_total"], 0.2)
        self.assertEqual(data["battery_discharge_energy_total"], 0.16)
        self.assertEqual(data["bms_pack_voltage"], 55.87)
        self.assertEqual(data["bms_pack_current"], 15.0)
        self.assertEqual(data["bms_pack_soc"], 97.0)
        self.assertEqual(data["bms_total_capacity"], 100.0)
        self.assertNotIn("inverter_throughput_energy", data)

    @unittest.skipUnless(HOMEASSISTANT_AVAILABLE, "homeassistant not installed")
    def test_normalize_telemetry_supports_power_first_ac_layout(self) -> None:
        poll_data = RawPollData(
            responses={
                "real": ParsedResponse(
                    command="real",
                    raw="real",
                    objects=[
                        {
                            "DevSN": "INV-1",
                            "Type": 80,
                            "SubType": 1035,
                            "workM": 1,
                            "ACin": [[2300], [100], [2500], [5000, 2500], [0]],
                            "ACout": [[2300], [100], [1500], [5000, 1500], [0]],
                            "PV": [[1000, 0, 0], [30, 0, 0], [300, 0, 0], [0]],
                            "Batt": [[52000], [50], [-200, 0]],
                            "Batsoc": [[8000, 0, 0]],
                        }
                    ],
                ),
                "basic": ParsedResponse(
                    command="basic",
                    raw="basic",
                    objects=[
                        {
                            "DevSN": "INV-1",
                            "Type": 80,
                            "version": "2.20",
                            "DSwVer": 200,
                            "DHwVer": 1000,
                        }
                    ],
                ),
                "set": ParsedResponse(command="set", raw="set", objects=[]),
            }
        )

        data = normalize_telemetry(poll_data)

        self.assertEqual(data["grid_import_power"], 2500)
        self.assertEqual(data["grid_frequency"], 50.0)
        self.assertEqual(data["load_power"], 1500)
        self.assertEqual(data["output_frequency"], 50.0)
        self.assertEqual(data["pv_power"], 300)
        self.assertEqual(data["pv_total_power"], 300)
        self.assertEqual(data["battery_charge_power"], 0)
        self.assertEqual(data["battery_discharge_power"], 200)

    @unittest.skipUnless(HOMEASSISTANT_AVAILABLE, "homeassistant not installed")
    def test_normalize_telemetry_clamps_flow_values(self) -> None:
        poll_data = RawPollData(
            responses={
                "real": ParsedResponse(
                    command="real",
                    raw="real",
                    objects=[
                        {
                            "DevSN": "INV-2",
                            "Type": 80,
                            "SubType": 1035,
                            "workM": 3,
                            "PV": [[1800, 0, 0], [100, 0, 0], [1000, 0, 0], [0]],
                            "ACin": [[2300], [0], [0], [0, 0], [0]],
                            "ACout": [[2300], [20], [500], [0, 0], [0]],
                            "Batt": [[52000], [50], [300, 0]],
                            "Batsoc": [[7000, 0, 0]],
                        }
                    ],
                ),
                "basic": ParsedResponse(
                    command="basic",
                    raw="basic",
                    objects=[{"DevSN": "INV-2", "Type": 80, "version": "2.20"}],
                ),
                "set": ParsedResponse(command="set", raw="set", objects=[]),
            }
        )

        data = normalize_telemetry(poll_data)

        self.assertEqual(data["pv_to_load_power"], 500)
        self.assertEqual(data["pv_to_battery_power"], 300)
        self.assertEqual(data["pv_to_grid_power"], 200)
        self.assertEqual(data["battery_to_load_power"], 0)
        self.assertEqual(data["grid_to_load_power"], 0)
        self.assertEqual(data["self_consumption_percent"], 80.0)
        self.assertEqual(data["battery_charge_power"], 300)
        self.assertEqual(data["battery_discharge_power"], 0)

    @unittest.skipUnless(HOMEASSISTANT_AVAILABLE, "homeassistant not installed")
    def test_normalize_telemetry_supports_per_string_pv_layout(self) -> None:
        poll_data = RawPollData(
            responses={
                "real": ParsedResponse(
                    command="real",
                    raw="real",
                    objects=[
                        {
                            "DevSN": "INV-3",
                            "Type": 80,
                            "SubType": 1035,
                            "PV": [[1200, 50, 600], [1100, 40, 440], [0, 0, 0], [1040]],
                            "Batt": [[52000], [0], [0, 0]],
                            "Batsoc": [[8000, 0, 0]],
                        }
                    ],
                ),
                "basic": ParsedResponse(
                    command="basic",
                    raw="basic",
                    objects=[{"DevSN": "INV-3", "Type": 80, "version": "2.20"}],
                ),
                "set": ParsedResponse(command="set", raw="set", objects=[]),
            }
        )

        data = normalize_telemetry(poll_data)

        self.assertEqual(data["pv1_voltage"], 120.0)
        self.assertEqual(data["pv1_current"], 5.0)
        self.assertEqual(data["pv1_power"], 600)
        self.assertEqual(data["pv2_voltage"], 110.0)
        self.assertEqual(data["pv2_current"], 4.0)
        self.assertEqual(data["pv2_power"], 440)
        self.assertEqual(data["pv3_voltage"], 0.0)
        self.assertEqual(data["pv3_current"], 0.0)
        self.assertEqual(data["pv3_power"], 0)
        self.assertEqual(data["pv_total_power"], 1040)
