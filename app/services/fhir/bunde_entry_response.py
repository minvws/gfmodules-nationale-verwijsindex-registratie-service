from fhir.resources.R4B.bundle import BundleEntryResponse
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.operationoutcome import OperationOutcome, OperationOutcomeIssue


def create_opertaion_outcome(severity: str, code: str, details: str) -> OperationOutcome:
    issue = OperationOutcomeIssue(code=code, severity=severity, details=CodeableConcept(text=details))
    return OperationOutcome(issue=[issue])


def create_bundle_response(status: int, severity: str, code: str, details: str) -> BundleEntryResponse:
    opertaion_outcome = create_opertaion_outcome(severity, code, details)
    return BundleEntryResponse(status=str(status), outcome=opertaion_outcome)
