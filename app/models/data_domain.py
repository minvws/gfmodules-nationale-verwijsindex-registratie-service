from dataclasses import dataclass
from typing import Any


@dataclass
class DataDomain:
    value: str

    def __init__(self, value: Any) -> None:
        self.value = str(value)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"DataDomain({self.value})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, DataDomain):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)
