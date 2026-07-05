"""Stale integracji elpiast_modbus."""

DOMAIN = "elpiast_modbus"
PLATFORMS = ["sensor", "binary_sensor", "number"]

CONF_UNIT_ID = "unit_id"
CONF_REGISTERS_FILE = "registers_file"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 30  # sekundy
