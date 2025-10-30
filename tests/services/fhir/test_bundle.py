from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryResponse

from app.services.fhir.bundle import BundleService


def test_from_entry_response_should_succeed() -> None:
    entry_response = BundleEntryResponse(status="CREATED")
    expected = Bundle(type="transaction-response", entry=[BundleEntry(response=entry_response)])
    actual = BundleService.from_entry_response([entry_response])

    assert expected == actual
