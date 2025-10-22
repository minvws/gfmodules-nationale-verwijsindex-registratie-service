from typing import Dict, List

from fhir.resources.R4B.bundle import Bundle, BundleEntry, BundleEntryResponse
from fhir.resources.R4B.domainresource import DomainResource
from fhir.resources.R4B.patient import Patient

from app.data import BSN
from app.exceptions.fhir_exception import FHIRException
from app.services.fhir.bunde_entry_response import create_bundle_response
from app.services.fhir.bundle import BundleService
from app.services.parsers.bundle import BundleParser
from app.services.parsers.patient import PatientParser
from app.services.parsers.reference import ReferenceParser
from app.services.registration.referrals import ReferralRegistrationService


class BundleRegistartionService:
    """
    Service that handles manual registration from FHIR Bundle.
    """

    def __init__(self, referrals_service: ReferralRegistrationService) -> None:
        self._referrals_service = referrals_service

    def register(self, bundle: Bundle) -> Bundle:
        data = self.make_map_data(bundle)

        responses: List[BundleEntryResponse] = []
        for res in data.values():
            # we skip patients
            if isinstance(res, Patient):
                continue

            # no reference for a patient
            reference = ReferenceParser.get_patient_reference(res)
            if reference is None:
                responses.append(
                    create_bundle_response(
                        status=400,
                        severity="error",
                        code="invalid",
                        details=f"no reference for patient found for {res.id}",
                    )
                )
                continue

            # not a valid relative reference
            ref_type, ref_id = ReferenceParser.get_reference_type_and_id(reference)
            if ref_type is None or ref_id is None:
                responses.append(
                    create_bundle_response(
                        status=400,
                        severity="error",
                        code="invalid",
                        details=f"reference for '{res.get_resource_type()}: {res.id}' is not relative, only relative references are allowed",
                    )
                )

                continue

            # not a valid reference for a patient (resources that have multiple types for a subject)
            if ref_type != "Patient":
                responses.append(
                    create_bundle_response(
                        status=400,
                        severity="error",
                        code="invalid",
                        details="reference is not a valid Patient reference",
                    )
                )

                continue

            patient = data.get(ref_id)

            # patient does not exist in bundle
            if patient is None:
                responses.append(
                    create_bundle_response(
                        status=400,
                        severity="error",
                        code="invalid",
                        details="Patient associated with resource does not exist in Bundle",
                    )
                )
                continue

            # not a valid patient model
            if not isinstance(patient, Patient):
                responses.append(
                    create_bundle_response(
                        status=400,
                        severity="error",
                        code="invalid",
                        details="Patient is not a valid Resource",
                    )
                )
                continue

            # cannot have a patient without an identifier
            if patient.identifier is None:
                responses.append(
                    create_bundle_response(
                        status=400,
                        severity="error",
                        code="invalid",
                        details="Patient without identifiers",
                    )
                )
                continue

            bsn_list = PatientParser.map_identifiers_to_bsn(patient.identifier)
            # only one bsn is allowed in patient
            if len(bsn_list) != 1:
                responses.append(
                    create_bundle_response(
                        status=400,
                        severity="error",
                        code="invalid",
                        details="Only one identifier with BSN system is allowed",
                    )
                )
                continue

            # TODO: validate bsn number at this point as well
            bsn_raw = bsn_list[0]
            try:
                bsn = BSN(bsn_raw)
            except ValueError as e:
                responses.append(
                    create_bundle_response(
                        status=400, severity="error", code="invalid", details=str(e)
                    )
                )
                continue

            referral = self._referrals_service.register(
                bsn=str(bsn), data_domain=res.get_resource_type()
            )
            if referral is None:
                responses.append(
                    create_bundle_response(
                        status=400,
                        severity="warning",
                        code="duplicate",
                        details="Record already exists",
                    )
                )

                continue

            responses.append(
                create_bundle_response(
                    status=201,
                    severity="information",
                    code="something-good",
                    details="Record created successfully",
                )
            )

        results = BundleService.from_entry_response(responses)
        return results

    def make_map_data(self, bundle: Bundle) -> Dict[str, DomainResource]:
        if not bundle.entry:
            raise FHIRException(
                status_code=400,
                severity="error",
                code="exception",
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
