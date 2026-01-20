import pytest
from unittest.mock import patch, MagicMock
from cryptography.hazmat.primitives.asymmetric import rsa
from typing import Any
from app.services.oauth.jwt_builder import JWTBuilder
from app.models.ura_number import UraNumber
import io
import builtins


DUMMY_CERT = b"-----BEGIN CERTIFICATE-----\nTESTCERT\n-----END CERTIFICATE-----\n"
DUMMY_KEY = b"-----BEGIN PRIVATE KEY-----\nTESTKEY\n-----END PRIVATE KEY-----\n"


@pytest.fixture
def ura_number() -> UraNumber:
    return UraNumber("12345678")


@pytest.fixture
def dummy_cert_file() -> str:
    return "dummy-cert.pem"


@pytest.fixture
def dummy_key_file() -> str:
    return "dummy-key.pem"


@pytest.fixture
def builder_args(dummy_cert_file: str, dummy_key_file: str, ura_number: UraNumber) -> dict[str, Any]:
    return {
        "endpoint": "https://example.com/token",
        "mtls_cert": dummy_cert_file,
        "ura_number": ura_number,
        "jwt_signing_cert": dummy_cert_file,
        "jwt_signing_key": dummy_key_file,
        "include_x5c": True,
    }


@pytest.fixture
def mock_open_file(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    def open_side_effect(path: str, mode: str = "rb", *args: Any, **kwargs: Any) -> io.BytesIO:
        if "key" in path:
            return io.BytesIO(DUMMY_KEY)
        return io.BytesIO(DUMMY_CERT)

    m: MagicMock = MagicMock(side_effect=open_side_effect)
    monkeypatch.setattr(builtins, "open", m)
    return m


@patch("app.services.oauth.jwt_builder.x509.load_pem_x509_certificate")
@patch("app.services.oauth.jwt_builder.serialization.load_pem_private_key")
@patch("app.services.oauth.jwt_builder.jwt.encode")
def test_jwt_builder_build_success(
    mock_jwt_encode: MagicMock,
    mock_load_key: MagicMock,
    mock_load_cert: MagicMock,
    builder_args: dict[str, Any],
    mock_open_file: MagicMock,
) -> None:
    mock_cert = MagicMock()
    mock_cert.public_bytes.return_value = b"cert-der-bytes"
    mock_load_cert.return_value = mock_cert
    mock_key = MagicMock(spec=rsa.RSAPrivateKey)
    mock_load_key.return_value = mock_key
    mock_jwt_encode.return_value = "jwt-token"

    builder = JWTBuilder(**builder_args)
    token = builder.build(target_audience="audience", scope="scope")

    assert token == "jwt-token"
    mock_jwt_encode.assert_called_once()
    mock_load_key.assert_called_once()
    mock_load_cert.assert_called()
    _, kwargs = mock_jwt_encode.call_args

    called_payload = kwargs["payload"]
    called_key = kwargs["key"]
    called_algorithm = kwargs["algorithm"]
    called_headers = kwargs["headers"]
    assert called_key is mock_load_key.return_value
    assert called_algorithm == "RS256"
    assert called_headers["typ"] == "JWT"
    assert called_headers["alg"] == "RS256"
    assert called_headers["kid"] == builder._jwt_signing_x5t_s256
    assert called_headers["x5c"] == builder._x5c_chain
    assert called_payload["iss"] == str(builder._ura_number)
    assert called_payload["sub"] == str(builder._ura_number)
    assert called_payload["aud"] == builder._endpoint
    assert called_payload["scope"] == "scope"
    assert called_payload["target_audience"] == "audience"
    assert "iat" in called_payload
    assert "exp" in called_payload
    assert "jti" in called_payload
    assert called_payload["cnf"]["x5t#S256"] == builder._mtls_x5t_s256


@patch("app.services.oauth.jwt_builder.x509.load_pem_x509_certificate")
@patch("app.services.oauth.jwt_builder.serialization.load_pem_private_key")
@patch("app.services.oauth.jwt_builder.jwt.encode")
def test_jwt_builder_x5c_chain_absent(
    mock_jwt_encode: MagicMock,
    mock_load_key: MagicMock,
    mock_load_cert: MagicMock,
    builder_args: dict[str, Any],
    mock_open_file: MagicMock,
) -> None:
    mock_jwt_encode.return_value = "jwt-token"
    builder_args["include_x5c"] = False
    mock_cert = MagicMock()
    mock_cert.public_bytes.return_value = b"cert-der-bytes"
    mock_load_cert.return_value = mock_cert
    mock_key = MagicMock(spec=rsa.RSAPrivateKey)
    mock_load_key.return_value = mock_key

    builder = JWTBuilder(**builder_args)
    assert builder._x5c_chain == []
    mock_load_key.assert_called_once()
    mock_load_cert.assert_called()
    builder.build(target_audience="audience", scope="scope")
    assert mock_jwt_encode.called
    _, kwargs = mock_jwt_encode.call_args
    headers = kwargs["headers"]
    assert "x5c" not in headers
