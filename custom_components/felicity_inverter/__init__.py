from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FelicityApiError, FelicityClient
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    PLATFORMS,
)
from .telemetry import normalize_telemetry

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class FelicityRuntimeData:
    """Runtime objects stored for a config entry."""

    client: FelicityClient
    coordinator: DataUpdateCoordinator[dict[str, Any]]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Felicity Inverter from YAML (unused)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Felicity Inverter config entry."""
    host = _entry_value(entry, CONF_HOST)
    port = _entry_int_value(entry, CONF_PORT, DEFAULT_PORT)
    scan_interval = max(
        _entry_int_value(entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        MIN_SCAN_INTERVAL,
    )

    if host is None:
        raise UpdateFailed("Missing host configuration")

    client = FelicityClient(host, port)

    async def _async_update_data() -> dict[str, Any]:
        try:
            raw_data = await client.async_fetch_data()
            return normalize_telemetry(raw_data, host=host, port=port)
        except FelicityApiError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = FelicityRuntimeData(
        client=client,
        coordinator=coordinator,
    )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Felicity Inverter config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _entry_value(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    return entry.options.get(key, entry.data.get(key, default))


def _entry_int_value(entry: ConfigEntry, key: str, default: int) -> int:
    value = _entry_value(entry, key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
