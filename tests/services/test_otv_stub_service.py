import builtins
from unittest.mock import MagicMock, mock_open, patch

import pytest
from requests.exceptions import ConnectionError

from app.models.permission import OtvStubPermissionRequest
from app.models.pseudonym import Pseudonym as PseudonymModel
from app.models.ura_number import UraNumber
from app.services.OtvService.otv_stub_service import OtvStubService, PermissionError

PATCHED_MODULE = "app.services.OtvService.otv_stub_service.GfHttpService.do_request"
PATCHED_URA_MODULE = "app.services.OtvService.otv_stub_service.UraNumber.from_certificate"

@pytest.fixture
def mock_otv_endpoint() -> str:
    return "https://example.com/otv"


@pytest.fixture
def mock_permission_request() -> OtvStubPermissionRequest:
    return OtvStubPermissionRequest(
        reversible_pseudonym=PseudonymModel(pseudonym="test-pseudonym-123"),
        client_ura_number=UraNumber("87654321"),
    )

@patch(PATCHED_URA_MODULE)
@patch.object(builtins, 'open', new_callable=mock_open, read_data="invalid-cert-data")
def test_otv_stub_service_initialization_fails_when_reading_cert_fails(
    mock_file: MagicMock,
    mock_ura_from_cert: MagicMock,
    mock_otv_endpoint: str
) -> None:
    
    mock_ura_from_cert.return_value = None
    with pytest.raises(PermissionError, match="Could not set UraNumber from mtls_cert"):
        OtvStubService(
            endpoint=mock_otv_endpoint,
            timeout=30,
            mtls_cert="/path/to/cert.pem",
            mtls_key=None,
            mtls_ca=None,
        )
    
    # Test with file not found by making open raise an exception
    mock_file.side_effect = FileNotFoundError("File not found")
    with pytest.raises(PermissionError, match="Could not set UraNumber from mtls_cert"):
        OtvStubService(
            endpoint=mock_otv_endpoint,
            timeout=30,
            mtls_cert="/nonexistent/path/cert.pem",
            mtls_key=None,
            mtls_ca=None,
        )

@patch(PATCHED_URA_MODULE)
@patch(PATCHED_MODULE)
@patch.object(builtins, 'open', new_callable=mock_open, read_data="valid-cert-data")
def test_check_authorization_succeeds_returns_true(
    mock_file: MagicMock,
    mock_do_request: MagicMock,
    mock_ura_from_cert: MagicMock,
    mock_otv_endpoint: str,
    mock_permission_request: OtvStubPermissionRequest,
) -> None:
    mock_ura_from_cert.return_value = UraNumber("12345678")
    mock_response = MagicMock()
    mock_response.json.return_value = True
    mock_do_request.return_value = mock_response

    service = OtvStubService(
        endpoint=mock_otv_endpoint,
        timeout=30,
        mtls_cert="/path/to/cert.pem",
        mtls_key=None,
        mtls_ca=None,
    )

    result = service.check_authorization(mock_permission_request)

    assert result is True
    mock_do_request.assert_called_once()

@patch(PATCHED_URA_MODULE)
@patch(PATCHED_MODULE)
@patch.object(builtins, 'open', new_callable=mock_open, read_data="valid-cert-data")
def test_check_authorization_succeeds_returns_false(
    mock_file: MagicMock,
    mock_do_request: MagicMock,
    mock_ura_from_cert: MagicMock,
    mock_otv_endpoint: str,
    mock_permission_request: OtvStubPermissionRequest,
) -> None:
    """Test successful authorization check that returns False"""
    mock_ura_from_cert.return_value = UraNumber("12345678")
    mock_response = MagicMock()
    mock_response.json.return_value = False
    mock_do_request.return_value = mock_response

    service = OtvStubService(
        endpoint=mock_otv_endpoint,
        timeout=30,
        mtls_cert="/path/to/cert.pem",
        mtls_key=None,
        mtls_ca=None,
    )

    result = service.check_authorization(mock_permission_request)

    assert result is False
    mock_do_request.assert_called_once()


@patch(PATCHED_URA_MODULE)
@patch(PATCHED_MODULE)
@patch.object(builtins, 'open', new_callable=mock_open, read_data="valid-cert-data")
def test_check_authorization_fails_on_connection_error(
    mock_file: MagicMock,
    mock_do_request: MagicMock,
    mock_ura_from_cert: MagicMock,
    mock_otv_endpoint: str,
    mock_permission_request: OtvStubPermissionRequest,
) -> None:
    mock_ura_from_cert.return_value = UraNumber("12345678")
    mock_do_request.side_effect = ConnectionError("Connection failed")

    service = OtvStubService(
        endpoint=mock_otv_endpoint,
        timeout=30,
        mtls_cert="/path/to/cert.pem",
        mtls_key=None,
        mtls_ca=None,
    )

    with pytest.raises(PermissionError, match="Failed to check for authorization"):
        service.check_authorization(mock_permission_request)

    mock_do_request.assert_called_once()

@patch(PATCHED_URA_MODULE)
@patch(PATCHED_MODULE)
@patch.object(builtins, 'open', new_callable=mock_open, read_data="valid-cert-data")
def test_check_authorization_fails_on_invalid_response_format(
    mock_file: MagicMock,
    mock_do_request: MagicMock,
    mock_ura_from_cert: MagicMock,
    mock_otv_endpoint: str,
    mock_permission_request: OtvStubPermissionRequest,
) -> None:
    mock_ura_from_cert.return_value = UraNumber("12345678")
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "unexpected format"}
    mock_do_request.return_value = mock_response

    service = OtvStubService(
        endpoint=mock_otv_endpoint,
        timeout=30,
        mtls_cert="/path/to/cert.pem",
        mtls_key=None,
        mtls_ca=None,
    )

    with pytest.raises(PermissionError, match="Failed to parse response"):
        service.check_authorization(mock_permission_request)

    mock_do_request.assert_called_once()
