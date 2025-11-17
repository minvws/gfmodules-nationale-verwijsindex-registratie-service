import logging

from fhir.resources.R4B.patient import Patient

from app.models.bsn import BSN
from app.models.permission import OtvStubPermissionRequest, PermissionRequestModel
from app.models.ura_number import UraNumber
from app.services.metadata import MetadataError, MetadataService
from app.services.OtvService.interface import OtvService
from app.services.parsers.patient import PatientParser
from app.services.pseudonym import PseudonymService

logger = logging.getLogger(__name__)


class PermissionCheckError(Exception):
    pass


class AuthorizationCheckService:
    def __init__(
        self,
        metadata_service: MetadataService,
        otv_service: OtvService,
        pseudonym_service: PseudonymService,
        otv_ura: UraNumber,
    ) -> None:
        self._otv_ura_number = otv_ura
        self._metadata_service = metadata_service
        self._otv_service = otv_service
        self._pseudonym_service = pseudonym_service

    def authorize(self, permission_request: PermissionRequestModel) -> bool:
        """
        Check if patient gave permission to share data
        1. Decrypt LMR ID
        2. Fetch Patient from LMR
        3. Extract BSN from Patient
        4. Create reversible pseudonym for OTV
        5. Check permission in OTV
        6. Return result
        """
        # Decrypt the LMR ID
        lmr_patient_id = self._decrypt_lmr_id(permission_request.encrypted_lmr_id)

        # Fetch patient from LMR
        patient = self._fetch_patient_from_lmr(lmr_patient_id)

        # Extract BSN from Patient
        bsn = self._extract_bsn_from_patient(patient)

        # Create OTV reversible pseudonym
        req = self._pseudonym_service.make_reversible_request_dto(
            bsn=bsn,
            recipient_organization_ura=permission_request.client_ura_number,
        )
        reversible_pseudonym = self._pseudonym_service.request_reversible(req)

        # Return check permission in OTV
        permission = self._check_permission_in_otv(
            OtvStubPermissionRequest(
                reversible_pseudonym=reversible_pseudonym,
                client_ura_number=permission_request.client_ura_number,
            )
        )
        return permission

    def _extract_bsn_from_patient(self, patient: Patient) -> BSN:
        try:
            bsns = PatientParser.map_identifiers_to_bsn(patient.identifier or [])
            if not bsns:
                logger.error("No BSN found for patient")
                raise ValueError("No BSN found for patient")
            if len(bsns) > 1:
                logger.error("Multiple BSNs found for patient")
                raise ValueError("Multiple BSNs found for patient")
            return BSN(bsns[0])
        except Exception as e:
            logger.error(f"Failed to extract BSN from patient: {e}")
            raise PermissionCheckError("Failed to extract BSN from patient") from e

    def _decrypt_lmr_id(self, encrypted_lmr_id: str) -> str:
        """
        Decrypt LMR ID with symmetric key
        """
        # Placeholder for decryption logic
        # TODO implement actual decryption
        return "default-1"

    def _fetch_patient_from_lmr(
        self,
        lmr_patient_id: str,
    ) -> Patient:
        """
        Fetch Patient from LMR
        """
        try:
            return self._metadata_service.get_patient(lmr_patient_id)
        except MetadataError as e:
            logger.error(f"Failed to fetch patient from LMR: {e}")
            raise PermissionCheckError("Fetching patient failed") from e

    def _check_permission_in_otv(
        self,
        permission_request: OtvStubPermissionRequest,
    ) -> bool:
        """
        Check if Patient gave permission to share data
        """
        try:
            return self._otv_service.check_authorization(permission_request)
        except PermissionError as e:
            logger.error(f"Failed to check permission in OTV: {e}")
        return False
