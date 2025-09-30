from typing import List, Tuple

from app.models.metadata.params import MetadataResourceParams
from app.services.api.fhir import FhirHttpService
from app.services.parsers.bundle import BundleParser
from app.services.parsers.patient import PatientParser


class MetadataService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        mtls_ca: str | None,
    ) -> None:
        self.http_service = FhirHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            mtls_ca=mtls_ca,
        )

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()

    # TODO: type the response
    def get_update_scheme(
        self, resource_type: str, last_updated: str | None = None
    ) -> Tuple[List[str], str | None]:
        params = MetadataResourceParams(
            _lastUpdated=f"ge{last_updated}" if last_updated else None,
            _include=f"{resource_type}:subject",
        )
        bundle = self.http_service.search(
            resource_type=resource_type,
            params=params.model_dump(by_alias=True, exclude_none=True),
        )

        latest_resource_update = BundleParser.get_latest_timestamp(bundle)
        if bundle.entry is None:
            return [], latest_resource_update

        patients = BundleParser.get_patients(bundle)
        identiefiers = PatientParser.get_identifiers(patients)

        matched_identifiers = [
            identifier.value for identifier in identiefiers if identifier.value
        ]
        return matched_identifiers, latest_resource_update
