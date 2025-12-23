from unittest.mock import MagicMock, patch

import pytest
from uzireader.uzi import UziException

from app.models.ura_number import UraNumber

PATCHED_MODULE = "app.models.ura_number.UziServer"


def test_create_ura_should_succeed() -> None:
    expected_value = "12345678"
    actual = UraNumber(expected_value)
    assert expected_value == actual.value


def test_create_ura_should_succeed_wiht_integers() -> None:
    expected_value = 12345678
    actual = UraNumber(expected_value)

    assert str(expected_value) == actual.value


def test_create_ura_number_should_succeed_with_fill() -> None:
    expected = UraNumber("1234")
    actual = UraNumber("1234")

    assert expected == actual


def test_create_should_fail_with_large_numbers() -> None:
    data = 12345678910
    with pytest.raises(ValueError):
        UraNumber(data)


def test_create_should_fail_with_non_digits() -> None:
    data = "123abc7"
    with pytest.raises(ValueError):
        UraNumber(data)


@patch(PATCHED_MODULE)
def test_from_certificate_should_succeed(mock_uzi_server: MagicMock) -> None:
    mock_data = {
        "commonName": "example",
        "OidCa": "example CA",
        "SubscriberNumber": "12345678",
    }
    mock_uzi_server.return_value = mock_data

    expected = UraNumber("12345678")
    actual = UraNumber.from_certificate("some-certificate")

    assert expected == actual


@patch(PATCHED_MODULE)
def test_from_certificate_should_return_none_when_extraction_fails(
    mock_uzi_server: MagicMock,
) -> None:
    mock_uzi_server.side_effect = UziException()

    actual = UraNumber.from_certificate("some-certificate")

    assert actual is None
