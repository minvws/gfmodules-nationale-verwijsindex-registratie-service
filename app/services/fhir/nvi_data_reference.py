from typing import Any, Dict

from app.models.referrals import CreateReferralRequest


class NviDataReferenceMapper:
    def __init__(
        self, pseudonym_system: str, source_system: str, organization_type_system: str, care_context_system: str
    ):
        self.pseudonym_system = pseudonym_system
        self.source_system = source_system
        self.organization_type_system = organization_type_system
        self.care_context_system = care_context_system

    def to_fhir(self, request: CreateReferralRequest) -> Dict[str, Any]:
        return {
            "resourceType": "NVIDataReference",
            "subject": {
                "system": self.pseudonym_system,
                "value": str(request.oprf_jwe.jwe),
            },
            "source": {
                "system": self.source_system,
                "value": str(request.ura_number.value),
            },
            "sourceType": {
                "coding": [
                    {
                        "system": self.organization_type_system,
                        "code": request.organization_type,
                        "display": request.organization_type.capitalize(),
                    }
                ]
            },
            "careContext": {
                "coding": [
                    {
                        "system": self.care_context_system,
                        "code": str(request.data_domain.value),
                    }
                ]
            },
            "oprfKey": request.blind_factor,
        }
