"""Platforma sensor dla EL-Piast Modbus."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VTSModbusCoordinator
from . import entry_slug


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VTSModbusCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VTSSensor(coordinator, entry, name)
        for name, reg in coordinator.registers.items()
        if reg.table in ("holding", "input") and reg.access == "read"
    ]
    async_add_entities(entities)


class VTSSensor(CoordinatorEntity[VTSModbusCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: VTSModbusCoordinator, entry: ConfigEntry, name: str) -> None:
        super().__init__(coordinator)
        self._name = name
        reg = coordinator.registers[name]

        self._attr_unique_id = f"{entry.entry_id}_{name}"
        self.entity_id = f"sensor.{entry_slug(entry)}_{name.lower()}"
        self._attr_translation_key = name
        self._attr_name = reg.description or name
        self._attr_native_unit_of_measurement = reg.unit or None
        self._attr_device_class = reg.device_class
        self._attr_state_class = reg.state_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="EL-Piast",
            model="Sterownik ELP11R32L MAX L (Modbus TCP/IP)",
        )

    @property
    def native_value(self):
        return self.coordinator.data.get(self._name)
