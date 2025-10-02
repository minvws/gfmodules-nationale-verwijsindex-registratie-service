from datetime import datetime
from typing import List

from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.domainresource import DomainResource
from fhir.resources.R4B.meta import Meta
from fhir.resources.R4B.patient import Patient


class BundleParser:
    @staticmethod
    def get_latest_timestamp(bundle: Bundle) -> str | None:
        if not bundle.entry:
            return None

        if len(bundle.entry) == 0:
            return None

        entries: List[BundleEntry] = bundle.entry
        update_timestamps = [BundleParser.get_timestamps(entry) for entry in entries if entry]
        filtered_update_timestamps = [ts for ts in update_timestamps if ts]

        latest_timestamp = max(filtered_update_timestamps).isoformat()
        return latest_timestamp

    @staticmethod
    def get_timestamps(entry: BundleEntry) -> datetime | None:
        if (
            entry.resource
            and isinstance(entry.resource, DomainResource)
            and entry.resource.meta
            and isinstance(entry.resource.meta, Meta)
            and entry.resource.meta.lastUpdated
            and isinstance(entry.resource.meta.lastUpdated, datetime)
        ):
            return entry.resource.meta.lastUpdated

        return None

    @staticmethod
    def get_patients(bundle: Bundle) -> List[Patient]:
        patients: List[Patient] = []
        if not bundle.entry:
            return []

        if len(bundle.entry) == 0:
            return []

        for entry in bundle.entry:
            if entry is None:
                continue

            if entry.resource and isinstance(entry.resource, Patient):
                patients.append(entry.resource)

        return patients
