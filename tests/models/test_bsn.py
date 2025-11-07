import hashlib
from typing import Any

import pytest

from app.models.bsn import BSN


@pytest.mark.parametrize(
    "valid_bsn",
    [
        "111222333",
        "123456782",
        123456782,
    ],
)
def test_valid_bsn_should_succeed(valid_bsn: Any) -> None:
    bsn = BSN(valid_bsn)
    assert str(bsn) == str(valid_bsn)
    assert repr(bsn) == f"BSN({str(valid_bsn)})"
    assert len(bsn.hash()) == 64


@pytest.mark.parametrize(
    "invalid_bsn,expected_error",
    [
        ("12345678", "BSN must be 9 digits"),
        ("1234567890", "BSN must be 9 digits"),
        ("abcdefghi", "invalid literal for int"),
        ("123456789", "Invalid BSN"),
    ],
)
def test_invalid_bsn_should_raise_exception(invalid_bsn: str, expected_error: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        BSN(invalid_bsn)
    assert expected_error.split()[0] in str(excinfo.value)


def test_bsn_hash_should_succeed() -> None:
    data = "123456782"
    bsn = BSN(data)
    expected = hashlib.sha256(data.encode()).hexdigest()

    actual = bsn.hash()

    assert expected == actual
