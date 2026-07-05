"""Coordinator odpowiadający za cykliczny odczyt i zapis rejestrów Modbus."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .registers import RegisterDefinition

_LOGGER = logging.getLogger(__name__)


class VTSModbusCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Odpytuje sterownik po Modbus TCP/IP i udostępnia dane encjom."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        unit_id: int,
        registers: Dict[str, RegisterDefinition],
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="EL-Piast Modbus",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.registers = registers
        self._client = None

    def _get_client(self):
        from pymodbus.client import ModbusTcpClient

        if self._client is None:
            self._client = ModbusTcpClient(host=self.host, port=self.port, timeout=5)
        if not self._client.is_socket_open():
            if not self._client.connect():
                raise ConnectionError(f"Nie udało się połączyć z {self.host}:{self.port}")
        return self._client

    # -- odczyt cykliczny (wywoływane przez DataUpdateCoordinator) --------
    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self._read_all_sync)
        except Exception as exc:  # noqa: BLE001
            raise UpdateFailed(f"Błąd komunikacji ze sterownikiem: {exc}") from exc

    def _read_all_sync(self) -> Dict[str, Any]:
        client = self._get_client()
        values: Dict[str, Any] = {}

        for name, reg in self.registers.items():
            if not reg.is_readable:
                continue
            try:
                values[name] = self._read_register_sync(client, reg)
            except Exception as exc:  # noqa: BLE001
                _LOGGER.warning("Nie udało się odczytać rejestru '%s': %s", name, exc)
                values[name] = None

        return values

    def _read_register_sync(self, client, reg: RegisterDefinition) -> Any:
        unit = self.unit_id
        if reg.table == "holding":
            result = client.read_holding_registers(reg.address, count=reg.register_count, slave=unit)
        elif reg.table == "input":
            result = client.read_input_registers(reg.address, count=reg.register_count, slave=unit)
        elif reg.table == "coil":
            result = client.read_coils(reg.address, count=1, slave=unit)
        elif reg.table == "discrete_input":
            result = client.read_discrete_inputs(reg.address, count=1, slave=unit)
        else:
            raise ValueError(f"Nieobsługiwana tabela: {reg.table}")

        if result.isError():
            raise IOError(f"Urządzenie zwróciło błąd: {result}")

        if reg.table in ("coil", "discrete_input"):
            return bool(result.bits[0])
        return reg.decode(result.registers)

    # -- zapis (wywoływane przez encje number) ----------------------
    async def async_write_register(self, name: str, value: Any) -> None:
        reg = self.registers[name]
        if not reg.is_writable:
            raise PermissionError(f"Rejestr '{name}' jest tylko do odczytu")

        await self.hass.async_add_executor_job(self._write_register_sync, reg, value)
        await self.async_request_refresh()

    def _write_register_sync(self, reg: RegisterDefinition, value: Any) -> None:
        client = self._get_client()
        unit = self.unit_id

        if reg.table == "coil":
            result = client.write_coil(reg.address, bool(value), slave=unit)
        elif reg.table == "holding":
            words = reg.encode(value)
            if len(words) == 1:
                result = client.write_register(reg.address, words[0], slave=unit)
            else:
                result = client.write_registers(reg.address, words, slave=unit)
        else:
            raise ValueError(f"Zapis do tabeli '{reg.table}' nie jest obsługiwany")

        if result.isError():
            raise IOError(f"Urządzenie zwróciło błąd przy zapisie: {result}")

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
