"""Definicje rejestrów Modbus oraz kodowanie/dekodowanie wartości."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RegisterDefinition:
    name: str
    address: int
    table: str = "holding"           # holding | input | coil | discrete_input
    data_type: str = "uint16"         # uint16 | int16 | uint32 | int32 | bitmask
    scale: float = 1.0
    unit: str = ""
    access: str = "read"               # read | write | read_write
    description: str = ""
    device_class: Optional[str] = None
    state_class: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None

    @property
    def register_count(self) -> int:
        return 2 if self.data_type in ("uint32", "int32") else 1

    @property
    def is_writable(self) -> bool:
        return self.access in ("write", "read_write")

    @property
    def is_readable(self) -> bool:
        return self.access in ("read", "read_write")

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "RegisterDefinition":
        return cls(
            name=name,
            address=int(data["address"]),
            table=data.get("table", "holding"),
            data_type=data.get("data_type", "uint16"),
            scale=float(data.get("scale", 1.0)),
            unit=data.get("unit", ""),
            access=data.get("access", "read"),
            description=data.get("description", ""),
            device_class=data.get("device_class"),
            state_class=data.get("state_class"),
            min=data.get("min"),
            max=data.get("max"),
            step=data.get("step"),
        )

    def decode(self, raw_registers) -> Any:
        if self.data_type == "uint16":
            value = raw_registers[0]
        elif self.data_type == "int16":
            value = raw_registers[0]
            if value >= 0x8000:
                value -= 0x10000
        elif self.data_type in ("uint32", "int32"):
            high, low = raw_registers[0], raw_registers[1]
            value = (high << 16) | low
            if self.data_type == "int32" and value >= 0x80000000:
                value -= 0x100000000
        elif self.data_type == "bitmask":
            return raw_registers[0]
        else:
            raise ValueError(f"Nieobsługiwany data_type: {self.data_type}")

        if self.scale != 1.0:
            value = round(value * self.scale, 6)
        return value

    def encode(self, value: Any):
        if self.scale != 1.0:
            value = int(round(value / self.scale))
        else:
            value = int(value)

        if self.data_type in ("uint16", "bitmask"):
            return [value & 0xFFFF]
        if self.data_type == "int16":
            if value < 0:
                value += 0x10000
            return [value & 0xFFFF]
        if self.data_type in ("uint32", "int32"):
            if value < 0:
                value += 0x100000000
            return [(value >> 16) & 0xFFFF, value & 0xFFFF]

        raise ValueError(f"Nieobsługiwany data_type: {self.data_type}")


def load_registers_from_yaml(path: str) -> Dict[str, RegisterDefinition]:
    """Ładuje mapę rejestrów z pliku YAML."""
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return {name: RegisterDefinition.from_dict(name, cfg) for name, cfg in data.items()}


def build_default_registers(raw: Dict[str, Dict[str, Any]]) -> Dict[str, RegisterDefinition]:
    return {name: RegisterDefinition.from_dict(name, cfg) for name, cfg in raw.items()}
