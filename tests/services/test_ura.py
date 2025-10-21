import builtins
from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.models.ura_number import UraNumber
from app.services.ura import UraNumberService, get_cert

PATCHED_CONFIG_MODULE = "app.services.ura.Config"
PATCHED_URA_MODULE = "app.services.ura.UraNumber"
PATCHED_CERT = "app.services.ura.get_cert"


@patch(PATCHED_CERT)
@patch(PATCHED_CONFIG_MODULE)
@patch(f"{PATCHED_URA_MODULE}.from_certificate")
def test_get_ura_number_should_succeed_from_cert(
    mock_ura_module: MagicMock, mock_config: MagicMock, mock_cert: MagicMock
) -> None:
    mock_config.referral_api.mtls_cert = "some-path"
    mock_cert.return_value = "some-cert"
    expected = UraNumber("12345678")
    mock_ura_module.return_value = expected

    actual = UraNumberService.get_ura_number(mock_config)

    assert expected == actual


@patch(PATCHED_CONFIG_MODULE)
def test_get_ura_number_should_raise_expection_when_it_cannot_find_cert_path(
    mock_config: MagicMock,
) -> None:
    mock_config.referral_api.mtls_cert = None
    with pytest.raises(RuntimeError):
        UraNumberService.get_ura_number(mock_config)


@patch(PATCHED_CONFIG_MODULE)
@patch(PATCHED_CERT)
def test_get_ura_number_shoud_raise_expcetion_with_cert_data_cannot_be_extracted(
    mock_cert: MagicMock,
    mock_config: MagicMock,
) -> None:
    mock_config.referral_api.mtls_cert = "some-path"
    mock_cert.return_value = None
    with pytest.raises(RuntimeError):
        UraNumberService.get_ura_number(mock_config)


@patch(PATCHED_CONFIG_MODULE)
@patch(PATCHED_CERT)
@patch(f"{PATCHED_URA_MODULE}.from_certificate")
def test_get_ura_number_should_raise_expection_when_ura_number_cannot_be_extracted_from_certificate(
    mock_ura_module: MagicMock, mock_cert: MagicMock, mock_config: MagicMock
) -> None:
    mock_config.referral_api.mtls_cert = "some-path"
    mock_cert.return_value = "some-cert"
    mock_ura_module.return_value = None
    with pytest.raises(RuntimeError):
        UraNumberService.get_ura_number(mock_config)


def test_get_cert_should_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = "some-cert"
    monkeypatch.setattr(builtins, "open", mock_open(read_data=expected))
    actual = get_cert("/some/path")

    assert expected == actual


def test_get_cert_should_return_None_when_exception_occurs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocked_open = mock_open(read_data="some-cert")
    mocked_open.side_effect = IOError
    monkeypatch.setattr(builtins, "open", mocked_open)
    actual = get_cert("/some/path")

    assert actual is None
