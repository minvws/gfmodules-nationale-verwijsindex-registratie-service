import hashlib
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


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


# DataDomain definitions
class DataDomain(Enum):
    Unknown = "unknown"
    BeeldBank = "beeldbank"
    MedicatieVerklaring = "medicatie verklaring"
    CarePlan = "zorgplan"

    @classmethod
    def get_all(cls) -> list["DataDomain"]:
        return [
            DataDomain.BeeldBank,
            DataDomain.MedicatieVerklaring,
            DataDomain.CarePlan,
        ]

    @classmethod
    def from_str(cls, label: str) -> Optional["DataDomain"]:
        try:
            return cls(label.lower())
        except ValueError:
            return None

    @classmethod
    def from_fhir(cls, label: str) -> Optional["DataDomain"]:
        match label:
            case "ImagingStudy":
                return DataDomain.BeeldBank
            case "MedicationStatement":
                return DataDomain.MedicatieVerklaring
            case "CarePlan":
                return DataDomain.CarePlan
            case _:
                return None

    def to_fhir(self) -> str:
        match self:
            case DataDomain.BeeldBank:
                return "ImagingStudy"
            case DataDomain.MedicatieVerklaring:
                return "MedicationStatement"
            case DataDomain.CarePlan:
                return "CarePlan"
            case _:
                return ""

    def __str__(self) -> str:
        return self.value
