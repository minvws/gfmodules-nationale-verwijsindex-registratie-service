import enum

from fhir.resources.R4B.bundle import BundleEntryResponse
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.operationoutcome import OperationOutcome, OperationOutcomeIssue

from app.data import (
    OutcomeResponseCode,
    OutcomeResponseSeverity,
    OutcomeResponseStatusCode,
)


def create_opertaion_outcome(severity: str, code: str, details: str) -> OperationOutcome:
    issue = OperationOutcomeIssue(code=code, severity=severity, details=CodeableConcept(text=details))
    return OperationOutcome(issue=[issue])


def create_bundle_response(status: int, severity: str, code: str, details: str) -> BundleEntryResponse:
    opertaion_outcome = create_opertaion_outcome(severity, code, details)
    return BundleEntryResponse(status=str(status), outcome=opertaion_outcome)


class KnownBundleRegistrationOutcome(enum.Enum):
    OK = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()


def create_known_response(outcome: KnownBundleRegistrationOutcome, details: str) -> BundleEntryResponse:
    match outcome:
        case KnownBundleRegistrationOutcome.OK:
            return create_bundle_response(
                status=OutcomeResponseStatusCode.CREATED.value,
                severity=OutcomeResponseSeverity.INFORMATION.value,
                code=OutcomeResponseCode.CREATED.value,
                details=details,
            )

        case KnownBundleRegistrationOutcome.WARNING:
            return create_bundle_response(
                status=OutcomeResponseStatusCode.BAD_REQUEST.value,
                severity=OutcomeResponseSeverity.WARNING.value,
                code=OutcomeResponseCode.DUPLICATE.value,
                details=details,
            )

        case KnownBundleRegistrationOutcome.ERROR:
            return create_bundle_response(
                status=OutcomeResponseStatusCode.BAD_REQUEST.value,
                severity=OutcomeResponseSeverity.ERROR.value,
                code=OutcomeResponseCode.INVALID.value,
                details=details,
            )
