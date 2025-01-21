from typing import Tuple

import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture
from starlette.requests import Request
from uzireader.uziserver import UziServer

from app.authentication import authenticated_ura, enforce_cert_newlines
from app.config import set_config
from app.data import UraNumber
from tests.test_config import get_test_config_with_postgres_db_connection


def test_ura_returns_subscriber_for_valid_cert(mocker: MockerFixture) -> None:
    set_config(get_test_config_with_postgres_db_connection())

    request = mocker.MagicMock(spec=Request)
    request.headers = {"x-proxy-ssl_client_cert": "cert-content"}

    uzi_server_mock = mocker.MagicMock(spec=UziServer)
    uzi_server_mock.__getitem__.side_effect = {"SubscriberNumber": 12345679}.__getitem__

    uzi_server_creation_mock = mocker.patch.object(UziServer, "__new__", return_value=uzi_server_mock)

    actual = authenticated_ura(request)

    assert actual == UraNumber(12345679)

    uzi_server_creation_mock.assert_called_once_with(
        UziServer,
        verify="SUCCESS",
        cert="-----BEGIN CERTIFICATE-----\ncert-content\n-----END CERTIFICATE-----",
    )
    uzi_server_mock.__getitem__.assert_called_with("SubscriberNumber")


def test_ura_auth_raises_exception_when_missing_cert_header(
    mocker: MockerFixture,
) -> None:
    request = mocker.MagicMock(spec=Request)
    request.headers = {}

    with pytest.raises(HTTPException):
        authenticated_ura(request)


def test_enforce_cert_newlines_with_headers(
    certificate_data: Tuple[str, str, str],
) -> None:
    cert_with_headers, _, expected_cert = certificate_data
    actual = enforce_cert_newlines(cert_with_headers)
    assert actual == expected_cert


def test_enforce_cert_newlines_without_headers(
    certificate_data: Tuple[str, str, str],
) -> None:
    _, cert_without_headers, expected_cert = certificate_data
    actual = enforce_cert_newlines(cert_without_headers)
    assert actual == expected_cert


@pytest.fixture
def certificate_data() -> Tuple[str, str, str]:
    cert_without_headers = (
        "000102030405060708091011121314151617181920212223242526272829303132333435363738394041424344454647484950"
    )
    cert_with_headers = f"-----BEGIN CERTIFICATE-----{cert_without_headers}-----END CERTIFICATE-----"
    expected_cert = "-----BEGIN CERTIFICATE-----\n0001020304050607080910111213141516171819202122232425262728293031\n32333435363738394041424344454647484950\n-----END CERTIFICATE-----"

    return cert_with_headers, cert_without_headers, expected_cert
