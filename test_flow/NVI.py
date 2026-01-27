from typing import Any

import requests


class NVI:
    def __init__(
        self, endpoint: str, mtls_cert: str, mtls_key: str, verify_ca: str | bool
    ) -> None:
        self.endpoint = endpoint
        self._mtls_cert = mtls_cert
        self._mtls_key = mtls_key
        self._verify_ca = verify_ca

    def register(
        self,
        ura_number: str,
        bearer_token: str,
        source_type: str,
        pseudonym: str,
        oprf_key: str,
        care_context: str,
    ) -> Any:
        """
        Register a referral in the NVI.
        """
        body = {
            "resourceType": "NVIDataReference",
            "source": {
                "system": "urn:oid:2.16.528.1.1007.3.3",
                "value": ura_number,
            },
            "sourceType": {
                "coding": [
                    {
                        "system": "http://vws.nl/fhir/CodeSystem/nvi-organization-types",
                        "code": source_type,
                    }
                ]
            },
            "careContext": {
                "coding": [
                    {"system": "http://nictiz.nl/fhir/hcim-2024", "code": care_context}
                ]
            },
            "subject": {
                "system": "http://vws.nl/fhir/NamingSystem/nvi-pseudonym",
                "value": pseudonym,
            },
            "oprfKey": oprf_key,
        }
        response = requests.post(
            f"{self.endpoint}/NVIDataReference",
            json=body,
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/fhir+json",
            },
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.json()

    def query(
        self,
        ura_number: str,
        bearer_token: str,
        pseudonym: str | None = None,
        oprf_key: str | None = None,
        care_context: str | None = None,
    ) -> Any:
        """
        Query NVIDataReferences in the NVI.
        Query on source ura_number, optionally pseudonym with oprf_key, and/or care_context.
        """
        params = {"source": ura_number}
        if pseudonym and oprf_key:
            params["pseudonym"] = pseudonym
            params["oprfKey"] = oprf_key
        if care_context:
            params["careContext"] = care_context

        response = requests.get(
            f"{self.endpoint}/NVIDataReference",
            params=params,
            headers={
                "Authorization": f"Bearer {bearer_token}",
            },
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.json()

    def get_by_id(self, reference_id: str, bearer_token: str) -> Any:
        """
        Get a specific NVIDataReference by its ID.
        """
        response = requests.get(
            f"{self.endpoint}/NVIDataReference/{reference_id}",
            headers={
                "Authorization": f"Bearer {bearer_token}",
            },
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.json()

    def delete(
        self,
        ura_number: str,
        bearer_token: str,
        pseudonym: str | None = None,
        oprf_key: str | None = None,
        care_context: str | None = None,
    ) -> Any:
        """
        Delete NVIDataReferences in the NVI.
        Delete on source ura_number, optionally pseudonym with oprf_key, and/or care_context.
        """
        params = {"source": ura_number}
        if pseudonym and oprf_key:
            params["pseudonym"] = pseudonym
            params["oprfKey"] = oprf_key
        if care_context:
            params["careContext"] = care_context

        response = requests.delete(
            f"{self.endpoint}/NVIDataReference",
            params=params,
            headers={
                "Authorization": f"Bearer {bearer_token}",
            },
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.status_code

    def delete_by_id(self, reference_id: str, bearer_token: str) -> Any:
        """
        Delete a specific NVIDataReference by its ID.
        """
        response = requests.delete(
            f"{self.endpoint}/NVIDataReference/{reference_id}",
            headers={
                "Authorization": f"Bearer {bearer_token}",
            },
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.json()

    def localize(
        self,
        bearer_token: str,
        pseudonym: str,
        oprf_key: str,
        care_context: str,
        source_type: list[str] | None = None,
    ) -> Any:
        """
        Localize a record in the NVI.
        """
        parameters = [
            {"name": "pseudonym", "valueString": pseudonym},
            {"name": "oprfKey", "valueString": oprf_key},
            {
                "name": "careContext",
                "valueCoding": {
                    "system": "http://nictiz.nl/fhir/hcim-2024",
                    "code": care_context,
                },
            },
        ]
        if source_type:
            for t in source_type:
                parameters.append({"name": "sourceType", "valueCode": t})
        body = {
            "resourceType": "Parameters",
            "parameter": parameters,
        }
        response = requests.post(
            f"{self.endpoint}/Organization/$localize",
            json=body,
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/fhir+json",
            },
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.json()
