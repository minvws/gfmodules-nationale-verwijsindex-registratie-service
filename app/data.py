import hashlib
import uuid
from dataclasses import dataclass
from typing import Any

# TODO: This should be in a system data or something
BSN_SYSTEM = "http://fhir.nl/fhir/NamingSystem/bsn"  # NOSONAR


@dataclass
class BSN:
    def __init__(self, value: Any) -> None:
        bsn = str(value)
        if len(bsn) != 9:
            raise ValueError("BSN must be 9 digits")

        total = sum(int(digit) * (9 - idx) for idx, digit in enumerate(bsn[:-1])) - int(bsn[-1])
        if total % 11 != 0:
            raise ValueError("Invalid BSN")

        self.value = bsn

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"BSN({self.value})"

    def hash(self) -> str:
        return hashlib.sha256(self.value.encode()).hexdigest()


@dataclass
class Pseudonym:
    def __init__(self, value: Any) -> None:
        self.value = uuid.UUID(str(value))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Pseudonym({self.value})"
