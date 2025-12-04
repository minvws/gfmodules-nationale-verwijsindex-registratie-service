from typing import Dict, List

from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryResponse
from fhir.resources.R4B.domainresource import DomainResource
from fhir.resources.R4B.patient import Patient

from app.data import (
    OutcomeResponseCode,
    OutcomeResponseSeverity,
    OutcomeResponseStatusCode,
)
from app.exceptions.fhir_exception import FHIRException
from app.models.bsn import BSN
from app.services.fhir.bunde_entry_response import (
    KnownBundleRegistrationOutcome,
    create_known_response,
)
from app.services.fhir.bundle import BundleService
from app.services.parsers.bundle import BundleParser
from app.services.parsers.patient import PatientParser
from app.services.parsers.reference import ReferenceParser
from app.services.registration.referrals import ReferralRegistrationService


class BundleRegistrationService:
    """
    Service that handles manual registration from FHIR Bundle.
    """

    def __init__(self, referrals_service: ReferralRegistrationService) -> None:
        self._referrals_service = referrals_service

    def register(self, bundle: Bundle) -> Bundle:
        data = self.make_map_data(bundle)

        responses: List[BundleEntryResponse] = []
        for res in data.values():
            # we skip patients in the map as we will handle them inside the register one
            if isinstance(res, Patient):
                continue

            response = self._register_one(res, data)
            responses.append(response)

        results = BundleService.from_entry_response(responses)
        return results

    def make_map_data(self, bundle: Bundle) -> Dict[str, DomainResource]:
        if not bundle.entry:
            raise FHIRException(
                status_code=OutcomeResponseStatusCode.BAD_REQUEST.value,
                severity=OutcomeResponseSeverity.ERROR.value,
                code=OutcomeResponseCode.EXCEPTION.value,
                msg="Invalid bundle without entries",
            )

        resources: List[DomainResource] = []
        for entry in bundle.entry:
            if not isinstance(entry, BundleEntry):
                continue

            res = BundleParser.get_resource(entry)
            if res is None:
                continue

            resources.append(res)
        ids = [res.id for res in resources if res.id]
        data_map = dict(zip(ids, resources))

        return data_map

    def _register_one(self, res: DomainResource, data: Dict[str, DomainResource]) -> BundleEntryResponse:
        # no reference for a patient
        reference = ReferenceParser.get_patient_reference(res)
        if reference is None:
            return create_known_response(
                KnownBundleRegistrationOutcome.ERROR,
                f"no reference for patient found for {res.id}",
            )

        # not a valid relative reference
        ref_type, ref_id = ReferenceParser.get_reference_type_and_id(reference)
        if ref_type is None or ref_id is None:
            return create_known_response(
                KnownBundleRegistrationOutcome.ERROR,
                f"reference for {res.get_resource_type()}: {res.id} is not relative, only relative references are allowed",
            )

        # not a valid reference for a patient (resources that have multiple types for a subject)
        if ref_type != "Patient":
            return create_known_response(
                KnownBundleRegistrationOutcome.ERROR,
                "Reference is not a valid Patient reference",
            )

        # patient does not exist in bundle
        patient = data.get(ref_id)
        if patient is None:
            return create_known_response(
                KnownBundleRegistrationOutcome.ERROR,
                "patient associated with resource does not exist in bundle",
            )

        # not a valid patient model
        if not isinstance(patient, Patient):
            return create_known_response(
                KnownBundleRegistrationOutcome.ERROR,
                "Patient is not a valid Resource",
            )

        # cannot have a patient without an identifier
        if patient.identifier is None:
            return create_known_response(
                KnownBundleRegistrationOutcome.ERROR,
                "Patient without identifiers",
            )

        bsn_list = PatientParser.map_identifiers_to_bsn(patient.identifier)
        # only one bsn is allowed in patient
        if len(bsn_list) != 1:
            return create_known_response(
                KnownBundleRegistrationOutcome.ERROR,
                "Only one identifier with BSN system is allowed",
            )

        bsn_raw = bsn_list[0]
        try:
            bsn = BSN(bsn_raw)
        except ValueError:
            return create_known_response(KnownBundleRegistrationOutcome.ERROR, "Invalid BSN number")

        referral = self._referrals_service.register(bsn=str(bsn), data_domain=res.get_resource_type())
        if referral is None:
            return create_known_response(KnownBundleRegistrationOutcome.WARNING, "Record already exists")

        return create_known_response(KnownBundleRegistrationOutcome.OK, "Record created successfully")
