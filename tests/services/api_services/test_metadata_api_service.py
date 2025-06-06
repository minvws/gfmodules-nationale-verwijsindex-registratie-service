from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.models.metadata.fhir import Bundle, Entry, Identifier, Link, Meta, Resource
from app.models.metadata.params import MetadataResourceParams
from app.models.referrals import ReferralQueryDTO
from app.services.api.metadata_api_service import BSN_SYSTEM, MetadataApiService
from app.services.api.nvi_api_service import NviApiService

PATCHED_MODULE = "app.services.api.api_service.ApiService._do_request"


@pytest.fixture
def imaging_study(datetime_past: str) -> Resource:
    return Resource(
        meta=Meta(lastUpdated=datetime_past),
        identifier=[Identifier(value="some_identifier", system="http://example.com")],
        resourceType="ImagingStudy",
    )


@pytest.fixture
def patient(mock_bsn_number: str, datetime_now: str) -> Resource:
    return Resource(
        meta=Meta(lastUpdated=datetime_now),
        identifier=[Identifier(value=mock_bsn_number, system=BSN_SYSTEM)],
        resourceType="Patient",
    )


@pytest.fixture
def patient_withou_bsn_system(mock_bsn_number: str, datetime_past: str) -> Resource:
    return Resource(
        meta=Meta(lastUpdated=datetime_past),
        identifier=[Identifier(value=mock_bsn_number, system="http://example.org")],
        resourceType="Patient",
    )


@pytest.fixture
def regular_bundle(imaging_study: Resource, patient: Resource) -> Bundle:
    return Bundle(
        link=[Link(relation="self", url="http://example.org")],
        entry=[Entry(resource=imaging_study), Entry(resource=patient)],
    )


@pytest.fixture
def bundle_without_bsn_system(imaging_study: Resource, patient_withou_bsn_system: Resource) -> Bundle:
    return Bundle(
        link=[Link(relation="self", url="http://example.org")],
        entry=[
            Entry(resource=imaging_study),
            Entry(resource=patient_withou_bsn_system),
        ],
    )


@pytest.fixture
def bundle_without_patient(imaging_study: Resource) -> Bundle:
    return Bundle(
        link=[Link(relation="self", url="http://example.org")],
        entry=[Entry(resource=imaging_study)],
    )


@pytest.fixture
def query_param() -> Dict[str, Any]:
    return MetadataResourceParams(_include="ImagingStudy:subject", _lastUpdated=datetime.now().isoformat()).model_dump(
        by_alias=True
    )


@pytest.fixture
def query_params_without_last_update() -> Dict[str, Any]:
    return MetadataResourceParams(_include="ImagingStudy:subject").model_dump(by_alias=True, exclude_none=True)


@pytest.fixture()
def fhir_error() -> Dict[str, Any]:
    return {
        "resourceType": "OperationOutcome",
        "issue": [{"severity": "error", "code": "some_error", "diagnostics": "some_error"}],
    }


@patch(PATCHED_MODULE)
def test_get_resource_bunlde_should_succed(
    mock_get: MagicMock,
    metadata_api_service: MetadataApiService,
    regular_bundle: Bundle,
    query_param: Dict[str, Any],
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = regular_bundle.model_dump()
    mock_response.params.return_value = query_param
    mock_get.return_value = mock_response

    actual = metadata_api_service.get_resource_bundle("ImagingStudy", query_param["_lastUpdated"])

    assert regular_bundle == actual

    mock_get.assert_called_once_with(
        method="GET",
        sub_route="fhir/ImagingStudy/_search",
        params={"_lastUpdated": f"ge{query_param['_lastUpdated']}", "_include": "ImagingStudy:subject"},
    )


@patch(PATCHED_MODULE)
def test_get_resource_bundle_without_last_update_bundle_should_succeed(
    mock_get: MagicMock,
    metadata_api_service: MetadataApiService,
    regular_bundle: Bundle,
    query_params_without_last_update: Dict[str, Any],
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = regular_bundle.model_dump()
    mock_response.params.return_value = query_params_without_last_update
    mock_get.return_value = mock_response

    actual = metadata_api_service.get_resource_bundle("ImagingStudy")

    assert regular_bundle == actual

    mock_get.assert_called_once_with(
        method="GET",
        sub_route="fhir/ImagingStudy/_search",
        params={"_include": "ImagingStudy:subject"},
    )


@patch(PATCHED_MODULE)
def test_get_update_scheme_should_succeed(
    mock_get: MagicMock,
    metadata_api_service: MetadataApiService,
    regular_bundle: Bundle,
    mock_bsn_number: str,
    datetime_now: str,
) -> None:
    expected_bsn_scheme, expected_latest_timestamp = (
        [mock_bsn_number],
        datetime_now,
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = regular_bundle.model_dump()
    mock_get.return_value = mock_response

    actual_bsn_scheme, actual_latest_timestamp = metadata_api_service.get_update_scheme("ImagingStudy")

    assert expected_bsn_scheme == actual_bsn_scheme
    assert expected_latest_timestamp == actual_latest_timestamp


@patch(PATCHED_MODULE)
def test_get_update_scheme_should_succeed_and_return_empty_list_and_timestamp_when_patient_has_no_bsn_system(
    mock_get: MagicMock,
    metadata_api_service: MetadataApiService,
    bundle_without_bsn_system: Bundle,
    datetime_past: str,
) -> None:
    expected_bsn_scheme, expected_latest_timestamp = [], datetime_past  # type: ignore
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = bundle_without_bsn_system.model_dump()
    mock_get.return_value = mock_response

    actual_bsn_scheme, actual_latest_timestamp = metadata_api_service.get_update_scheme("ImagingStudy")
    assert expected_bsn_scheme == actual_bsn_scheme
    assert expected_latest_timestamp == actual_latest_timestamp
    mock_get.assert_called_once()


@patch(PATCHED_MODULE)
def test_get_update_scheme_should_succeed_and_return_empty_list_when_bundle_has_no_patient(
    mock_get: MagicMock,
    metadata_api_service: MetadataApiService,
    bundle_without_patient: Bundle,
    datetime_past: str,
) -> None:
    expected_bsn_scheme, expected_timestamp = [], datetime_past  # type: ignore
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = bundle_without_patient.model_dump()
    mock_get.return_value = mock_response

    actual_bsn_scheme, actual_timestamp = metadata_api_service.get_update_scheme("ImagingStudy")
    assert expected_bsn_scheme == actual_bsn_scheme
    assert expected_timestamp == actual_timestamp
    mock_get.assert_called_once()


@patch(PATCHED_MODULE)
def test_get_referrals_should_return_none_if_not_found(
    mock_post: MagicMock,
    nvi_api_service: NviApiService,
    referral_query: ReferralQueryDTO,
) -> None:
    mock_post.side_effect = requests.HTTPError("Not Found")

    actual = nvi_api_service.get_referrals(referral_query)

    mock_post.assert_called_once_with(
        method="POST",
        sub_route="registrations/query",
        data=referral_query.model_dump(),
    )
    assert actual is None


@patch(PATCHED_MODULE)
def test_get_referrals_should_return_none_if_connection_timedout(
    mock_post: MagicMock,
    nvi_api_service: NviApiService,
    referral_query: ReferralQueryDTO,
) -> None:
    mock_post.side_effect = requests.Timeout

    actual = nvi_api_service.get_referrals(referral_query)

    mock_post.assert_called_once_with(
        method="POST",
        sub_route="registrations/query",
        data=referral_query.model_dump(),
    )
    assert actual is None


@patch(PATCHED_MODULE)
def test_get_refferals_should_fail_when_connection_is_not_established(
    mock_post: MagicMock,
    nvi_api_service: NviApiService,
    referral_query: ReferralQueryDTO,
) -> None:
    mock_post.side_effect = ConnectionError

    actual = nvi_api_service.get_referrals(referral_query)

    mock_post.assert_called_once_with(
        method="POST",
        sub_route="registrations/query",
        data=referral_query.model_dump(),
    )
    assert actual is None
