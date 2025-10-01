from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fhir.resources.R4B.bundle import Bundle
from requests import HTTPError

from app.services.api.fhir import FhirHttpService

PATCHED_MODULE = "app.services.api.fhir.HttpService.do_request"


@patch(PATCHED_MODULE)
def test_search_should_with_params_succed(
    mock_get: MagicMock,
    fhir_http_service: FhirHttpService,
    regular_bundle: Bundle,
    query_param: Dict[str, Any],
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = regular_bundle.model_dump()
    mock_response.params.return_value = query_param
    mock_get.return_value = mock_response

    actual = fhir_http_service.search("ImagingStudy", query_param)

    assert regular_bundle == actual

    mock_get.assert_called_once_with(
        method="GET",
        sub_route="ImagingStudy/_search",
        params=query_param,
    )


@patch(PATCHED_MODULE)
def test_search_should_succeed_without_params(
    mock_get: MagicMock,
    fhir_http_service: FhirHttpService,
    regular_bundle: Bundle,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = regular_bundle.model_dump()
    mock_get.return_value = mock_response

    actual = fhir_http_service.search("ImagingStudy")

    assert regular_bundle == actual

    mock_get.assert_called_once_with(method="GET", sub_route="ImagingStudy/_search", params=None)


@patch(PATCHED_MODULE)
def test_get_resource_bundle_without_last_update_bundle_should_succeed(
    mock_get: MagicMock,
    fhir_http_service: FhirHttpService,
    regular_bundle: Bundle,
    query_params_without_last_update: Dict[str, Any],
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = regular_bundle.model_dump()
    mock_response.params.return_value = query_params_without_last_update
    mock_get.return_value = mock_response

    actual = fhir_http_service.search(resource_type="ImagingStudy", params=query_params_without_last_update)

    assert regular_bundle == actual

    mock_get.assert_called_once_with(
        method="GET",
        sub_route="ImagingStudy/_search",
        params={"_include": "ImagingStudy:subject"},
    )


@patch(PATCHED_MODULE)
def test_search_should_fail_with_error_status_code(mock_get: MagicMock, fhir_http_service: FhirHttpService) -> None:
    mock_get.side_effect = HTTPError()
    with pytest.raises(HTTPError):
        fhir_http_service.search("ImagingStudy")
