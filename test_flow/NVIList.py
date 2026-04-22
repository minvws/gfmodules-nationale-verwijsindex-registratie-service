from typing import Any

import requests


class NVIList:
    def __init__(
        self,
        endpoint: str,
        mtls_cert: str,
        mtls_key: str,
        verify_ca: str | bool,
        url_prefix: str = "/v1-poc",
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self._mtls_cert = mtls_cert
        self._mtls_key = mtls_key
        self._verify_ca = verify_ca
        self._url_prefix = url_prefix.rstrip("/")

    @staticmethod
    def _identifier_value(system: str, value: str) -> str:
        return f"{system}|{value}"

    def _headers(self, bearer_token: str, include_content_type: bool = False) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        if include_content_type:
            headers["Content-Type"] = "application/fhir+json"
        return headers

    def create(self, body: dict[str, Any], bearer_token: str) -> Any:
        """
        Create a new FHIR List entry.
        """
        response = requests.post(
            f"{self.endpoint}{self._url_prefix}/fhir/List",
            json=body,
            headers=self._headers(bearer_token, include_content_type=True),
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        print(response.status_code, response.text)
        response.raise_for_status()
        return response.json()

    def get_by_id(self, list_id: str, bearer_token: str) -> Any:
        """
        Get a specific FHIR List entry by its ID.
        """
        response = requests.get(
            f"{self.endpoint}{self._url_prefix}/fhir/List/{list_id}",
            headers=self._headers(bearer_token),
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.json()

    def query(
        self,
        bearer_token: str,
        subject_system: str | None = None,
        subject_value: str | None = None,
        code: str | None = None,
        source_system: str | None = None,
        source_value: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Query FHIR List entries.
        """
        params: dict[str, Any] = {}
        if subject_system and subject_value:
            params["subject:identifier"] = self._identifier_value(subject_system, subject_value)
        if source_system and source_value:
            params["source:identifier"] = self._identifier_value(source_system, source_value)
        if code:
            params["code"] = code
        if extra_params:
            params.update(extra_params)

        response = requests.get(
            f"{self.endpoint}{self._url_prefix}/fhir/List",
            params=params,
            headers=self._headers(bearer_token),
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.json()

    def delete(
        self,
        bearer_token: str,
        subject_system: str | None = None,
        subject_value: str | None = None,
        code: str | None = None,
        source_system: str | None = None,
        source_value: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> int:
        """
        Delete FHIR List entries by query.
        """
        params: dict[str, Any] = {}
        if subject_system and subject_value:
            params["subject:identifier"] = self._identifier_value(subject_system, subject_value)
        if source_system and source_value:
            params["source:identifier"] = self._identifier_value(source_system, source_value)
        if code:
            params["code"] = code
        if extra_params:
            params.update(extra_params)

        response = requests.delete(
            f"{self.endpoint}{self._url_prefix}/fhir/List",
            params=params,
            headers=self._headers(bearer_token),
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.status_code

    def delete_by_id(self, list_id: str, bearer_token: str) -> int:
        """
        Delete a specific FHIR List entry by ID.
        """
        response = requests.delete(
            f"{self.endpoint}{self._url_prefix}/fhir/List/{list_id}",
            headers=self._headers(bearer_token),
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.status_code

    def transaction(self, bundle: dict[str, Any], bearer_token: str) -> Any:
        """
        Execute a FHIR transaction bundle against the NVI FHIR endpoint.
        """
        response = requests.post(
            f"{self.endpoint}{self._url_prefix}/fhir",
            json=bundle,
            headers=self._headers(bearer_token, include_content_type=True),
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        return response.json()
