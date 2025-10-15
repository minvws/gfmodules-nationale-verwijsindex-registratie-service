from enum import Enum
from typing import Optional


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
