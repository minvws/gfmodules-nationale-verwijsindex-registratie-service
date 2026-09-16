from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.patient import Patient

from app.data import BSN_SYSTEM


class PatientParser:
    @staticmethod
    def get_identifiers(patients: list[Patient]) -> list[Identifier]:
        return [identifier for patient in patients if patient.identifier for identifier in patient.identifier]

    @staticmethod
    def map_identifiers_to_bsn(identifiers: list[Identifier]) -> list[str]:
        return [
            identifier.value
            for identifier in identifiers
            if identifier.value and identifier.system and identifier.system == BSN_SYSTEM
        ]
