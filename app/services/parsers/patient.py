from typing import List

from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.patient import Patient

from app.data import BSN_SYSTEM


class PatientParser:
    @staticmethod
    def get_identifiers(patients: List[Patient]) -> List[Identifier]:
        return [identifier for patient in patients if patient.identifier for identifier in patient.identifier]

    @staticmethod
    def map_identifiers_to_bsn(identifiers: List[Identifier]) -> List[str]:
        return [
            identifier.value
            for identifier in identifiers
            if identifier.value and identifier.system and identifier.system == BSN_SYSTEM
        ]
