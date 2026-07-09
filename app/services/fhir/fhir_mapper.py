from typing import Any, Dict, List
from uuid import UUID

from app.models.referrals import Referral


class FhirMapper:
    def __init__(
        self,
        extension_identifier: str,
        extension_url: str,
        subject_system: str,
        source_system: str,
    ) -> None:
        self.extension_identifier = extension_identifier
        self.extension_url = extension_url
        self.subject_system = subject_system
        self.source_system = source_system

    def from_fhir_bundle(self, bundle: Dict[str, Any]) -> List[Referral]:
        """
        Extracts relevant data from a FHIR bundle with List resources
        """
        referrals = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "List":
                referral = self.from_list_resource(resource)
                referrals.append(referral)
        return referrals

    def from_list_resource(self, resource: Dict[str, Any]) -> Referral:
        """
        Extracts relevant data from a FHIR List resource
        """
        ura_number = resource.get("extension", [{}])[0].get("valueReference", {}).get("identifier", {}).get("value")
        source_id = resource.get("source", {}).get("identifier", {}).get("value")
        res_id = resource.get("id")

        return Referral(
            id=UUID(res_id),
            ura_number=ura_number,
            source_id=source_id,
        )

    def to_list_resource(
        self,
        ura_number: str,
        subject: str,
        source_id: str | None = None,
    ) -> Dict[str, Any]:
        resource = {
            "resourceType": "List",
            "extension": [
                {
                    "valueReference": {
                        "identifier": {
                            "system": self.extension_identifier,
                            "value": ura_number,
                        }
                    },
                    "url": self.extension_url,
                }
            ],
            "subject": {"identifier": {"system": self.subject_system, "value": subject}},
            "status": "current",
            "mode": "working",
            "emptyReason": {
                "coding": [
                    {
                        "code": "withheld",
                        "system": "http://terminology.hl7.org/CodeSystem/list-empty-reason",
                    }
                ]
            },
        }
        if source_id:
            resource["source"] = {"identifier": {"system": self.source_system, "value": source_id}}
        return resource
