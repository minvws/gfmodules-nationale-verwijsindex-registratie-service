from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, Timeout

from app.services.api.http_service import HttpService


class MockHttpService(HttpService):
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        mtls_ca: str | None,
    ):
        super().__init__(endpoint, timeout, mtls_cert, mtls_key, mtls_ca)

    def server_healthy(self) -> bool:
        return True


@pytest.fixture
def mock_body() -> Dict[str, Any]:
    return {"some_key": "some_value"}


@pytest.fixture
def mock_params() -> Dict[str, Any]:
    return {"param1": "value1", "param2": "value2"}


@pytest.fixture
def mock_sub_route() -> str:
    return "sub/route/path"


PATCHED_MODULE = "app.services.api.http_service.request"


@patch(PATCHED_MODULE)
def test_do_request_should_succeed(
    mock_post: MagicMock,
    http_service: HttpService,
    mock_body: Dict[str, Any],
) -> None:
    mock_request = MagicMock()
    mock_request.status_code = 200
    mock_request.json.return_value = mock_body
    mock_post.return_value = mock_request

    actual = http_service.do_request(method="POST", data=mock_body)

    assert actual.json() == mock_body
    assert actual.status_code == 200
    mock_post.assert_called_once()


@patch(PATCHED_MODULE)
def test_do_request_should_succeed_with_query_params(
    mock_get: MagicMock,
    http_service: HttpService,
    mock_params: Dict[str, Any],
    mock_body: Dict[str, Any],
    mock_url: str,
) -> None:
    expected_url = f"{mock_url}?param1={mock_params['param1']}&param2={mock_params['param2']}"
    mock_request = MagicMock()
    mock_request.status_code = 200
    mock_request.json.return_value = mock_body
    mock_request.url = expected_url
    mock_get.return_value = mock_request
    actual = http_service.do_request(method="GET", params=mock_params)

    assert actual.json() == mock_body
    assert actual.status_code == 200
    assert actual.url == expected_url


@patch(PATCHED_MODULE)
def test_do_request_should_succeed_with_sub_routes(
    mock_get: MagicMock, http_service: HttpService, mock_url: str, mock_sub_route: str
) -> None:
    expected_url = f"{mock_url}/{mock_sub_route}"
    mock_request = MagicMock()
    mock_request.status_code = 201
    mock_request.url = expected_url
    mock_get.return_value = mock_request

    actual = http_service.do_request(method="GET", sub_route=mock_sub_route)

    assert actual.url == expected_url


@patch(PATCHED_MODULE)
def test_do_request_should_fail_on_timeout(
    mock_request: MagicMock,
    http_service: HttpService,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_request.side_effect = Timeout("Timeout Error")

    with pytest.raises(Exception) as e:
        http_service.do_request("GET")

    assert "Timeout" in str(e.value)
    assert "Request failed:" in caplog.text
    assert "Timeout Error" in caplog.text


@patch(PATCHED_MODULE)
def test_do_request_should_fail_on_connection_error(
    mock_request: MagicMock,
    http_service: HttpService,
    mock_sub_route: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_request.side_effect = ConnectionError("Connection Error")

    with pytest.raises(Exception) as e:
        http_service.do_request(method="DELETE", sub_route=mock_sub_route)

    assert "Connection Error" in str(e.value)
    assert "Request failed:" in caplog.text
    assert "Connection Error" in caplog.text


@patch(PATCHED_MODULE)
def do_request_should_fail_with_unkown_request_methods(
    http_service: HttpService,
) -> None:
    with pytest.raises(Exception):
        http_service.do_request("SOME-METHOD")  # type: ignore


@patch(PATCHED_MODULE)
def test_do_request_should_use_mtls_cert_when_enabled(
    mock_request: MagicMock,
    mock_url: str,
) -> None:
    api_service = MockHttpService(
        endpoint=mock_url,
        timeout=10,
        mtls_cert="test.crt",
        mtls_key="test.key",
        mtls_ca="test.ca",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    api_service.do_request("GET", mock_url)

    mock_request.assert_called_once()
    call_kwargs = mock_request.call_args[1]
    assert call_kwargs["cert"] == ("test.crt", "test.key")
    assert call_kwargs["verify"]


@patch(PATCHED_MODULE)
def test_do_request_should_use_ca_file_for_verification_when_provided(
    mock_request: MagicMock,
    mock_url: str,
) -> None:
    api_service = MockHttpService(
        endpoint=mock_url,
        timeout=10,
        mtls_cert="test.crt",
        mtls_key="test.key",
        mtls_ca="ca.crt",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    api_service.do_request("GET", mock_url)

    mock_request.assert_called_once()
    call_kwargs = mock_request.call_args[1]
    assert call_kwargs["cert"] == ("test.crt", "test.key")
    assert call_kwargs["verify"]


@patch(PATCHED_MODULE)
def test_do_request_should_not_use_cert_when_mtls_disabled(
    mock_request: MagicMock,
    mock_url: str,
) -> None:
    api_service = MockHttpService(endpoint=mock_url, timeout=10, mtls_cert=None, mtls_key=None, mtls_ca=None)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    api_service.do_request("GET", mock_url)

    mock_request.assert_called_once()
    call_kwargs = mock_request.call_args[1]
    assert call_kwargs["cert"] is None
    assert call_kwargs["verify"] is True
