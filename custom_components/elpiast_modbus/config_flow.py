"""Config flow dla integracji EL-Piast Modbus."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_REGISTERS_FILE,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
)
from .registers import load_registers_from_yaml

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        vol.Optional(CONF_REGISTERS_FILE): str,
    }
)


async def _validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> None:
    """Sprawdza połączenie TCP oraz (opcjonalnie) poprawność pliku rejestrów."""
    from pymodbus.client import ModbusTcpClient

    registers_file: Optional[str] = data.get(CONF_REGISTERS_FILE)
    if registers_file:
        try:
            registers = await hass.async_add_executor_job(load_registers_from_yaml, registers_file)
        except Exception as exc:  # noqa: BLE001
            raise InvalidRegistersFile from exc
        if not registers:
            raise InvalidRegistersFile

    def _test_connection() -> bool:
        client = ModbusTcpClient(host=data[CONF_HOST], port=data[CONF_PORT], timeout=5)
        ok = client.connect()
        client.close()
        return ok

    connected = await hass.async_add_executor_job(_test_connection)
    if not connected:
        raise CannotConnect


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow EL-Piast Modbus."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        errors: Dict[str, str] = {}

        if user_input is not None:
            unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:{user_input[CONF_UNIT_ID]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                await _validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidRegistersFile:
                errors["base"] = "invalid_registers_file"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Nieoczekiwany błąd walidacji")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Centrala EL-Piast ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Błąd sygnalizujący brak połączenia z urządzeniem."""


class InvalidRegistersFile(HomeAssistantError):
    """Błąd sygnalizujący niepoprawny plik z mapą rejestrów."""
