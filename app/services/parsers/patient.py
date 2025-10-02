from typing import List

from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.patient import Patient


class PatientParser:
    @staticmethod
    def get_identifiers(patients: List[Patient]) -> List[Identifier]:
        return [identifier for patient in patients if patient.identifier for identifier in patient.identifier]
