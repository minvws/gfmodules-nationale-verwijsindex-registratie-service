from fhir.resources.R4B.bundle import BundleEntryResponse
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.operationoutcome import OperationOutcome, OperationOutcomeIssue

from app.services.fhir.bunde_entry_response import (
    create_bundle_response,
    create_opertaion_outcome,
)


def test_create_operation_outcome_should_succeed() -> None:
    issue = OperationOutcomeIssue(code="some-code", severity="error", details=CodeableConcept(text="some-text"))
    expected = OperationOutcome(issue=[issue])

    actual = create_opertaion_outcome(severity="error", code="some-code", details="some-text")

    assert expected == actual


def test_create_bundle_response_should_succeed() -> None:
    operation_outcome = create_opertaion_outcome(severity="error", code="some-code", details="some-details")
    expected = BundleEntryResponse(status="400", outcome=operation_outcome)

    actual = create_bundle_response(status=400, severity="error", code="some-code", details="some-details")

    assert expected == actual
