import itertools
from datetime import datetime
from typing import List

from app.models.metadata.fhir import Bundle, Entry, Identifier
from app.models.metadata.params import MetadataResourceParams
from app.services.api.http_service import HttpService

BSN_SYSTEM = "http://fhir.nl/fhir/NamingSystem/bsn"


class MetadataApiService(HttpService):
    def server_healthy(self) -> bool:
        return self._server_healthy("actuator/health")

    def get_resource_bundle(self, resource_type: str, last_updated: str | None = None) -> Bundle:
        params = MetadataResourceParams(
            _lastUpdated=f"ge{last_updated}" if last_updated else None,
            _include=f"{resource_type}:subject",
        )
        response = self.do_request(
            method="GET",
            sub_route=f"fhir/{resource_type}/_search",
            params=params.model_dump(by_alias=True, exclude_none=True),
        )
        data = response.json()
        return Bundle(**data)

    def get_update_scheme(self, resource_type: str, last_updated: str | None = None) -> tuple[list[str], str | None]:
        bundle = self.get_resource_bundle(resource_type, last_updated)
        entries = bundle.entry
        last_resource_update = self.get_latest_timestamp_from_bundle(entries) if entries is not None else None
        if entries is None:
            return [], last_resource_update

        patients = list(filter(self.filter_patients, entries))
        if len(patients) == 0:
            return [], last_resource_update

        patients_identifiers = list(itertools.chain.from_iterable(map(self.get_resource_identifier, patients)))

        return [
            identifier.value for identifier in patients_identifiers if identifier.system == BSN_SYSTEM
        ], last_resource_update

    def get_latest_timestamp_from_bundle(self, entries: List[Entry]) -> str | None:
        if len(entries) == 0:
            return None

        update_timestamps = list(
            map(
                lambda x: datetime.fromisoformat(x.resource.meta.last_updated),
                entries,
            )
        )
        return max(update_timestamps).isoformat()

    @staticmethod
    def filter_patients(entry: Entry) -> bool:
        if entry.resource.resource_type == "Patient":
            identifiers = entry.resource.identifier or []
            if any(identifier.system == BSN_SYSTEM for identifier in identifiers):
                return True

        return False

    @staticmethod
    def get_resource_identifier(entry: Entry) -> List[Identifier]:
        if entry.resource.identifier is not None:
            return entry.resource.identifier

        return []
