from unittest.mock import MagicMock, patch

import pytest
from fhir.resources.R4B.patient import Patient

from app.models.bsn import BSN
from app.models.permission import OtvStubPermissionRequest, PermissionRequestModel
from app.models.pseudonym import Pseudonym as PseudonymModel
from app.models.pseudonym import ReversiblePseudonymRequest
from app.services.authorization_check_service import AuthorizationCheckService, PermissionCheckError
from app.services.metadata import MetadataError
from fhir.resources.R4B.identifier import Identifier
from app.data import BSN_SYSTEM

PATCH_LMR_ID_DECRYPT = "app.services.authorization_check_service.AuthorizationCheckService._decrypt_lmr_id"


@pytest.fixture
def mock_permission_request() -> PermissionRequestModel:
    return PermissionRequestModel(
        encrypted_lmr_id="encrypted-lmr-id-sample",
        client_ura_number="12345678",
    )


@pytest.fixture
def rev_pseudonym_request(
    mock_bsn_number: str, mock_permission_request: PermissionRequestModel
) -> ReversiblePseudonymRequest:
    return ReversiblePseudonymRequest(
        personal_id=mock_bsn_number,
        recipient_organization=str(mock_permission_request.client_ura_number),
        recipient_scope="OtvService",
        pseudonym_type="reversible",
    )


@pytest.fixture
def pseudonym_model() -> PseudonymModel:
    return PseudonymModel(pseudonym="reversible-pseudonym-sample")


@pytest.fixture
def mock_otv_permission_request(
    pseudonym_model: PseudonymModel,
    mock_permission_request: PermissionRequestModel,
) -> OtvStubPermissionRequest:
    return OtvStubPermissionRequest(
        reversible_pseudonym=pseudonym_model,
        client_ura_number=mock_permission_request.client_ura_number,
    )


@patch(PATCH_LMR_ID_DECRYPT)
def test_authorize_succeeds(
    mock_decrypt_lmr_id: MagicMock,
    auth_check_service: AuthorizationCheckService,
    mock_permission_request: PermissionRequestModel,
    patient: Patient,
    mock_bsn_number: str,
    rev_pseudonym_request: ReversiblePseudonymRequest,
    pseudonym_model: PseudonymModel,
    mock_otv_permission_request: OtvStubPermissionRequest,
) -> None:
    mock_decrypt_lmr_id.return_value = "decrypted-lmr-id-sample"
    auth_check_service._metadata_service.get_patient.return_value = patient # type: ignore 
    auth_check_service._pseudonym_service.make_reversible_request_dto.return_value = rev_pseudonym_request # type: ignore
    auth_check_service._pseudonym_service.request_reversible.return_value = pseudonym_model # type: ignore
    auth_check_service._otv_service.check_authorization.return_value = True # type: ignore

    authorized = auth_check_service.authorize(mock_permission_request)

    auth_check_service._metadata_service.get_patient.assert_called_once_with("decrypted-lmr-id-sample") # type: ignore
    assert authorized
    assert auth_check_service._decrypt_lmr_id.call_count == 1 # type: ignore
    auth_check_service._pseudonym_service.make_reversible_request_dto.assert_called_once_with( # type: ignore
        bsn=BSN(mock_bsn_number),
        recipient_organization_ura=mock_permission_request.client_ura_number,
    )
    auth_check_service._pseudonym_service.request_reversible.assert_called_once_with(rev_pseudonym_request) # type: ignore
    auth_check_service._otv_service.check_authorization.assert_called_once_with(mock_otv_permission_request) # type: ignore


def test_extract_bsn_from_patient_fails_with_no_identifier(patient: Patient) -> None:
    patient.identifier = None
    
    auth_service = AuthorizationCheckService(
        metadata_service=MagicMock(),
        otv_service=MagicMock(),
        pseudonym_service=MagicMock(),
        otv_ura=MagicMock(),
    )
    
    with pytest.raises(PermissionCheckError, match="Failed to extract BSN from patient"):
        auth_service._extract_bsn_from_patient(patient)

def test_extract_bsn_from_patient_fails_with_multiple_bsns(patient: Patient) -> None:
    patient.identifier = [
        Identifier(system=BSN_SYSTEM, value="200060429"),
        Identifier(system=BSN_SYSTEM, value="200060442"),
    ]
    
    auth_service = AuthorizationCheckService(
        metadata_service=MagicMock(),
        otv_service=MagicMock(),
        pseudonym_service=MagicMock(),
        otv_ura=MagicMock(),
    )
    
    with pytest.raises(PermissionCheckError, match="Failed to extract BSN from patient"):
        auth_service._extract_bsn_from_patient(patient)

def test_extract_bsn_from_patient_fails_with_invalid_bsn(patient: Patient, mock_bsn_number: str) -> None:
    from fhir.resources.R4B.identifier import Identifier
    from app.data import BSN_SYSTEM
    
    patient.identifier = [Identifier(system=BSN_SYSTEM, value="123456789")]
    
    auth_service = AuthorizationCheckService(
        metadata_service=MagicMock(),
        otv_service=MagicMock(),
        pseudonym_service=MagicMock(),
        otv_ura=MagicMock(),
    )
    
    with pytest.raises(PermissionCheckError, match="Failed to extract BSN from patient"):
        auth_service._extract_bsn_from_patient(patient)

def test_extract_bsn_from_patient_succeeds(patient: Patient, mock_bsn_number: str) -> None:
    auth_service = AuthorizationCheckService(
        metadata_service=MagicMock(),
        otv_service=MagicMock(),
        pseudonym_service=MagicMock(),
        otv_ura=MagicMock(),
    )
    
    bsn = auth_service._extract_bsn_from_patient(patient)
    
    assert bsn.value == mock_bsn_number
    assert isinstance(bsn, BSN)

def test_fetch_patient_from_lmr_fails_on_exception(
    auth_check_service: AuthorizationCheckService,
) -> None:
    auth_check_service._metadata_service.get_patient.side_effect = MetadataError("Failed to fetch patient") # type: ignore
    
    with pytest.raises(PermissionCheckError, match="Fetching patient failed"):
        auth_check_service._fetch_patient_from_lmr("some-lmr-id")

def test_check_permission_in_otv_returns_false_on_exception(
    auth_check_service: AuthorizationCheckService,
    mock_otv_permission_request: OtvStubPermissionRequest,
) -> None:
    auth_check_service._otv_service.check_authorization.side_effect = PermissionError("OTV permission check failed") # type: ignore
    
    # Should return False instead of raising an exception
    result = auth_check_service._check_permission_in_otv(mock_otv_permission_request)
    
    assert result is False
    auth_check_service._otv_service.check_authorization.assert_called_once_with(mock_otv_permission_request) # type: ignore