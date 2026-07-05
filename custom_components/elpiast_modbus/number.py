"""Platforma number dla EL-Piast Modbus (zapisywalne nastawy)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
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
        VTSNumber(coordinator, entry, name)
        for name, reg in coordinator.registers.items()
        if reg.table == "holding" and reg.is_writable
    ]
    async_add_entities(entities)


class VTSNumber(CoordinatorEntity[VTSModbusCoordinator], NumberEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: VTSModbusCoordinator, entry: ConfigEntry, name: str) -> None:
        super().__init__(coordinator)
        self._name = name
        reg = coordinator.registers[name]

        self._attr_unique_id = f"{entry.entry_id}_{name}"
        self.entity_id = f"number.{entry_slug(entry)}_{name.lower()}"
        self._attr_translation_key = name
        self._attr_name = reg.description or name
        self._attr_native_unit_of_measurement = reg.unit or None
        self._attr_native_min_value = reg.min if reg.min is not None else 0
        self._attr_native_max_value = reg.max if reg.max is not None else 100
        self._attr_native_step = reg.step if reg.step is not None else 1
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="EL-Piast",
            model="Sterownik ELP11R32L MAX L (Modbus TCP/IP)",
        )

    @property
    def native_value(self):
        return self.coordinator.data.get(self._name)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_register(self._name, value)
