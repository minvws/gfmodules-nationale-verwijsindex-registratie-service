from typing import List

from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryResponse


class BundleService:
    @staticmethod
    def from_entry_response(data: List[BundleEntryResponse]) -> Bundle:
        entries = [BundleEntry(response=response) for response in data]
        return Bundle(type="transaction-response", entry=entries)
