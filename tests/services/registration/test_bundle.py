from unittest.mock import MagicMock, patch

import pytest
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.imagingstudy import ImagingStudy
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.reference import Reference

from app.data import (
    BSN_SYSTEM,
)
from app.exceptions.fhir_exception import FHIRException
from app.models.referrals import Referral
from app.services.fhir.bunde_entry_response import (
    KnownBundleRegistrationOutcome,
    create_known_response,
)
from app.services.registration.bundle import BundleRegistrationService

PATCHED_MODULE = "app.services.registration.bundle.ReferralRegistrationService.register"


def test_make_map_should_succeed(
    bundle_registration_service: BundleRegistrationService,
) -> None:
    patient = Patient(id="patient-1")
    imaging_study = ImagingStudy.model_construct(
        id="imaging-study-1", subject=Reference(reference="Patient/patient-id")
    )
    bundle = Bundle(
        type="transaction",
        entry=[BundleEntry(resource=patient), BundleEntry(resource=imaging_study)],
    )
    expected = {"patient-1": patient, "imaging-study-1": imaging_study}

    actual = bundle_registration_service.make_map_data(bundle)

    assert expected == actual


def test_make_map_should_raise_exception_when_bundle_has_no_entries(
    bundle_registration_service: BundleRegistrationService,
) -> None:
    bundle = Bundle(type="transaction")
    with pytest.raises(FHIRException):
        bundle_registration_service.make_map_data(bundle)


@patch(PATCHED_MODULE)
def test_register_should_succeed(
    referral_response: MagicMock,
    bundle_registration_service: BundleRegistrationService,
    mock_referral: Referral,
    regular_bundle: Bundle,
) -> None:
    referral_response.return_value = mock_referral
    expected = Bundle(
        type="transaction-response",
        entry=[
            BundleEntry(
                response=create_known_response(KnownBundleRegistrationOutcome.OK, "Record created successfully")
            )
        ],
    )

    actual = bundle_registration_service.register(regular_bundle)

    assert expected == actual


@patch(PATCHED_MODULE)
def test_register_should_return_a_duplicate_warning_response_when_referral_exist(
    referral_response: MagicMock,
    bundle_registration_service: BundleRegistrationService,
    regular_bundle: Bundle,
) -> None:
    referral_response.return_value = None
    expected = Bundle(
        type="transaction-response",
        entry=[
            BundleEntry(response=create_known_response(KnownBundleRegistrationOutcome.WARNING, "Record already exists"))
        ],
    )

    actual = bundle_registration_service.register(regular_bundle)

    assert expected == actual


def test_register_should_return_error_response_when_patient_has_invalid_bsn(
    bundle_registration_service: BundleRegistrationService,
) -> None:
    identifier = Identifier(system=BSN_SYSTEM, value="some-broken-bsn")
    patient = Patient.model_construct(id="patient-1", identifier=[identifier])
    imaging_study = ImagingStudy.model_construct(
        id="imaging-study-id", subject=Reference(reference="Patient/patient-1")
    )
    bundle = Bundle(
        type="transaction",
        entry=[BundleEntry(resource=imaging_study), BundleEntry(resource=patient)],
    )
    expected = Bundle(
        type="transaction-response",
        entry=[BundleEntry(response=create_known_response(KnownBundleRegistrationOutcome.ERROR, "Invalid BSN number"))],
    )

    actual = bundle_registration_service.register(bundle)

    assert expected == actual


def test_register_without_bsn_should_return_error_response(
    bundle_registration_service: BundleRegistrationService,
    bundle_without_bsn_system: Bundle,
) -> None:
    expected = Bundle(
        type="transaction-response",
        entry=[
            BundleEntry(
                response=create_known_response(
                    KnownBundleRegistrationOutcome.ERROR,
                    "Only one identifier with BSN system is allowed",
                )
            )
        ],
    )

    actual = bundle_registration_service.register(bundle_without_bsn_system)

    assert expected == actual


def test_register_without_identifier_in_patient_should_return_error_response(
    bundle_registration_service: BundleRegistrationService,
) -> None:
    patient = Patient.model_construct(id="patient-1")
    imaging_study = ImagingStudy.model_construct(
        id="imaging-study-id", subject=Reference(reference="Patient/patient-1")
    )
    bundle = Bundle(
        type="transaction",
        entry=[BundleEntry(resource=imaging_study), BundleEntry(resource=patient)],
    )
    expected = Bundle(
        type="transaction-response",
        entry=[
            BundleEntry(
                response=create_known_response(
                    KnownBundleRegistrationOutcome.ERROR,
                    "Patient without identifiers",
                )
            )
        ],
    )

    actual = bundle_registration_service.register(bundle)

    assert expected == actual


def test_register_without_patient_should_return_error_response(
    bundle_without_patient: Bundle,
    bundle_registration_service: BundleRegistrationService,
) -> None:
    expected = Bundle(
        type="transaction-response",
        entry=[
            BundleEntry(
                response=create_known_response(
                    KnownBundleRegistrationOutcome.ERROR,
                    "patient associated with resource does not exist in bundle",
                )
            )
        ],
    )

    actual = bundle_registration_service.register(bundle_without_patient)

    assert expected == actual


def test_register_without_relative_reference_to_not_patient_should_return_error_response(
    bundle_registration_service: BundleRegistrationService,
) -> None:
    imaging_study = ImagingStudy.model_construct(
        id="imaging-study-1",
        subject=Reference(reference="Group/group-1"),
    )
    bundle = Bundle(type="transaction", entry=[BundleEntry(resource=imaging_study)])
    expected = Bundle(
        type="transaction-response",
        entry=[
            BundleEntry(
                response=create_known_response(
                    KnownBundleRegistrationOutcome.ERROR,
                    "Reference is not a valid Patient reference",
                )
            )
        ],
    )

    actual = bundle_registration_service.register(bundle)

    assert expected == actual


def test_register_with_contained_references_should_return_error_response(
    bundle_registration_service: BundleRegistrationService,
) -> None:
    imaging_study = ImagingStudy.model_construct(id="imaging-study-1", subject=Reference(reference="#patient-1"))
    bundle = Bundle(type="transaction", entry=[BundleEntry(resource=imaging_study)])
    expected = Bundle(
        type="transaction-response",
        entry=[
            BundleEntry(
                response=create_known_response(
                    KnownBundleRegistrationOutcome.ERROR,
                    f"reference for {imaging_study.get_resource_type()}: {imaging_study.id} is not relative, only relative references are allowed",
                )
            )
        ],
    )

    actual = bundle_registration_service.register(bundle)

    assert expected == actual


def test_registter_without_reference_to_patient_should_return_error_response(
    bundle_registration_service: BundleRegistrationService,
) -> None:
    imaging_study = ImagingStudy.model_construct(id="imaging-study-1", subject=None)
    bundle = Bundle(type="transaction", entry=[BundleEntry(resource=imaging_study)])
    expected = Bundle(
        type="transaction-response",
        entry=[
            BundleEntry(
                response=create_known_response(
                    KnownBundleRegistrationOutcome.ERROR,
                    f"no reference for patient found for {imaging_study.id}",
                )
            )
        ],
    )

    actual = bundle_registration_service.register(bundle)

    assert expected == actual
