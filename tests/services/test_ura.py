from unittest.mock import MagicMock, patch

import pytest

from app.models.ura_number import UraNumber
from app.services.ura import UraNumberService

PATCHED_CONFIG_MODULE = "app.services.ura.Config"
PATCHED_URA_MODULE = "app.services.ura.UraNumber"
PATCHED_CERT = "app.services.ura.get_cert"


@patch(PATCHED_CERT)
@patch(PATCHED_CONFIG_MODULE)
@patch(f"{PATCHED_URA_MODULE}.from_certificate")
def test_get_ura_should_succeed_from_cert(
    mock_ura_module: MagicMock, mock_config: MagicMock, mock_cert: MagicMock
) -> None:
    mock_config.referral_api.mtls_ca = "some-path"
    mock_cert.return_value = "some-cert"
    expected = UraNumber("12345678")
    mock_ura_module.return_value = expected

    actual = UraNumberService.get_ura_number(mock_config)

    assert expected == actual


@patch(PATCHED_CERT)
@patch(PATCHED_CONFIG_MODULE)
@patch(f"{PATCHED_URA_MODULE}.from_certificate")
def test_get_ura_should_default_to_config_when_io_error_occurs(
    mock_ura_module: MagicMock,
    mock_config: MagicMock,
    mock_cert: MagicMock,
) -> None:
    mock_config.referral_api.mtls_ca = "some-corrupted-path"
    mock_config.app.ura_number = "123456"
    mock_cert.return_value = None
    mock_ura_module.return_value = None
    expected = UraNumber("123456")

    actual = UraNumberService.get_ura_number(mock_config)

    assert expected == actual


@patch(PATCHED_CONFIG_MODULE)
def test_get_ura_should_default_to_config_when_no_cert_path_exist(
    mock_config: MagicMock,
) -> None:
    mock_config.referral_api.mtls_ca = None
    mock_config.app.ura_number = "45678"
    expected = UraNumber("45678")

    actual = UraNumberService.get_ura_number(mock_config)

    assert expected == actual


@patch(PATCHED_CONFIG_MODULE)
def test_get_ura_should_raise_expection_when_it_cannot_find_ura_in_cert_and_in_config(
    mock_config: MagicMock,
) -> None:
    mock_config.referral_api.mtls_ca = None
    mock_config.app.ura_number = None
    with pytest.raises(RuntimeError):
        UraNumberService.get_ura_number(mock_config)
