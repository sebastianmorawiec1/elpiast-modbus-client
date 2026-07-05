"""Integracja EL-Piast Modbus dla Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from pathlib import Path

from .const import (
    CONF_REGISTERS_FILE,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import VTSModbusCoordinator
from .registers import load_registers_from_yaml


def entry_slug(entry: ConfigEntry) -> str:
    """Stabilny prefiks entity_id na podstawie hosta, np. elp_192_168_1_70."""
    host = str(entry.data.get(CONF_HOST, "elp")).lower()
    return "elp_" + "".join(ch if ch.isalnum() else "_" for ch in host)

# Domyślna mapa rejestrów: pełna mapa z oficjalnej DTR EL-PIAST MAX L+ v6.4, dołączona do integracji.
BUNDLED_REGISTERS_FILE = Path(__file__).parent / "registers_elpiast_maxl.yaml"

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data

    registers_file = data.get(CONF_REGISTERS_FILE) or str(BUNDLED_REGISTERS_FILE)
    registers = await hass.async_add_executor_job(load_registers_from_yaml, registers_file)

    coordinator = VTSModbusCoordinator(
        hass,
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        unit_id=data[CONF_UNIT_ID],
        registers=registers,
        scan_interval=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator: VTSModbusCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(coordinator.close)
    return unloaded
