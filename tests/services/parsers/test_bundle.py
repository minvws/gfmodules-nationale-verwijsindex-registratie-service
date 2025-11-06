from datetime import datetime
from typing import Any, Dict, List

import pytest
from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.bodystructure import BodyStructure
from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.R4B.careplan import CarePlan
from fhir.resources.R4B.careteam import CareTeam
from fhir.resources.R4B.clinicalimpression import ClinicalImpression
from fhir.resources.R4B.detectedissue import DetectedIssue
from fhir.resources.R4B.diagnosticreport import DiagnosticReport
from fhir.resources.R4B.domainresource import DomainResource
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.familymemberhistory import FamilyMemberHistory
from fhir.resources.R4B.imagingstudy import ImagingStudy
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.immunizationevaluation import ImmunizationEvaluation
from fhir.resources.R4B.immunizationrecommendation import ImmunizationRecommendation
from fhir.resources.R4B.measurereport import MeasureReport
from fhir.resources.R4B.medicationadministration import MedicationAdministration
from fhir.resources.R4B.medicationdispense import MedicationDispense
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.medicationstatement import MedicationStatement
from fhir.resources.R4B.molecularsequence import MolecularSequence
from fhir.resources.R4B.nutritionorder import (
    NutritionOrder,
)
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.organization import Organization
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.procedure import Procedure
from fhir.resources.R4B.reference import Reference
from fhir.resources.R4B.riskassessment import RiskAssessment

from app.services.fhir.bunde_entry_response import create_bundle_response
from app.services.parsers.bundle import BundleParser


@pytest.fixture
def mock_bundle_without_entries() -> Dict[str, Any]:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [{"relation": "self", "url": "http://example.org"}],
    }


@pytest.fixture
def bundle_without_entries(mock_bundle_without_entries: Dict[str, Any]) -> Bundle:
    return Bundle.model_validate(mock_bundle_without_entries)


def test_get_latest_time_stamp_shoud_succeed(regular_bundle: Bundle, datetime_now: str) -> None:
    actual = BundleParser.get_latest_timestamp(regular_bundle)

    assert datetime_now == actual


def test_get_latest_time_stamp_should_return_none_whith_bundle_without_entries(
    bundle_without_entries: Bundle,
) -> None:
    actual = BundleParser.get_latest_timestamp(bundle_without_entries)

    assert actual is None


def test_get_timestamp_should_succeed(regular_bundle: Bundle, datetime_now: str) -> None:
    # typechecker happy
    assert regular_bundle.entry
    assert len(regular_bundle.entry) > 0

    entry = regular_bundle.entry[0]

    actual = BundleParser.get_timestamps(entry)

    assert datetime.fromisoformat(datetime_now) == actual


def test_get_timestamp_should_return_none_with_entry_without_resource() -> None:
    entry = BundleEntry.model_construct()

    actual = BundleParser.get_timestamps(entry)

    assert actual is None


def test_get_patients_should_succeed(regular_bundle: Bundle, patient: Patient) -> None:
    expected = [patient]

    actual = BundleParser.get_patients(regular_bundle)

    assert expected == actual


def test_get_patients_should_return_empty_list_when_no_entries_in_bundle(
    bundle_without_entries: Bundle,
) -> None:
    expected: List[Patient] = []

    actual = BundleParser.get_patients(bundle_without_entries)

    assert expected == actual


def test_get_resource_should_return_domain_resources() -> None:
    expected = Organization(id="some-id", active=True)
    entry = BundleEntry(resource=expected)

    actual = BundleParser.get_resource(entry)

    assert expected == actual
    assert isinstance(actual, DomainResource)


def test_get_resource_should_return_none_when_entry_has_no_domain_resources() -> None:
    entry_response = create_bundle_response(200, "good", "good-code", details="you did good")
    entry = BundleEntry(response=entry_response)

    actual = BundleParser.get_resource(entry)

    assert actual is None


@pytest.mark.parametrize(
    "resource, expected",
    [
        (
            AllergyIntolerance.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            BodyStructure.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            ImagingStudy.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            CarePlan.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            CareTeam.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            ClinicalImpression.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            DetectedIssue.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            DiagnosticReport.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            Encounter.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            MedicationStatement.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            Immunization.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            FamilyMemberHistory.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            ImmunizationEvaluation.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            ImmunizationRecommendation.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            MeasureReport.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            MedicationAdministration.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            MedicationDispense.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            MedicationRequest.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            MolecularSequence.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            NutritionOrder.model_construct(patient=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            Observation.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            Procedure.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
        (
            RiskAssessment.model_construct(subject=Reference(reference="Patient/1")),
            Reference(reference="Patient/1"),
        ),
    ],
)
def test_get_patient_reference_should_succeed(resource: DomainResource, expected: Reference) -> None:
    entry = BundleEntry(resource=resource)
    actual = BundleParser.get_patient_reference(entry)

    assert expected == actual


def test_get_patient_reference_should_return_none_when_no_entry_exist() -> None:
    entry = BundleEntry(request=BundleEntryRequest(method="POST", url="http://example.org"))

    actual = BundleParser.get_patient_reference(entry)

    assert actual is None


def test_get_patient_reference_should_return_none_when_a_resource_is_not_referencing_a_patient() -> None:
    org = Organization(id="some-id")
    entry = BundleEntry(resource=org)

    actual = BundleParser.get_patient_reference(entry)

    assert actual is None
