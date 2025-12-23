from unittest.mock import MagicMock, patch

from fhir.resources.R4B.bundle import Bundle

from app.models.data_domain import DataDomain
from app.services.metadata import MetadataService

PATCHED_MODULE = "app.services.metadata.FhirHttpService.do_request"


@patch(PATCHED_MODULE)
def test_get_update_scheme_should_succeed(
    mock_get: MagicMock,
    metadata_service: MetadataService,
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

    actual_bsn_scheme, actual_latest_timestamp = metadata_service.get_update_scheme(DataDomain("ImagingStudy"))

    assert expected_bsn_scheme == actual_bsn_scheme
    assert expected_latest_timestamp == actual_latest_timestamp


@patch(PATCHED_MODULE)
def test_get_update_scheme_should_succeed_and_return_empty_list_and_timestamp_when_patient_has_no_bsn_system(
    mock_get: MagicMock,
    metadata_service: MetadataService,
    bundle_without_bsn_system: Bundle,
    datetime_past: str,
) -> None:
    expected_bsn_scheme, expected_latest_timestamp = [], datetime_past  # type: ignore
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = bundle_without_bsn_system.model_dump()
    mock_get.return_value = mock_response

    actual_bsn_scheme, actual_latest_timestamp = metadata_service.get_update_scheme(DataDomain("ImagingStudy"))
    assert expected_bsn_scheme == actual_bsn_scheme
    assert expected_latest_timestamp == actual_latest_timestamp
    mock_get.assert_called_once()


@patch(PATCHED_MODULE)
def test_get_update_scheme_should_succeed_and_return_empty_list_when_bundle_has_no_patient(
    mock_get: MagicMock,
    metadata_service: MetadataService,
    bundle_without_patient: Bundle,
    datetime_past: str,
) -> None:
    expected_bsn_scheme, expected_timestamp = [], datetime_past  # type: ignore
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = bundle_without_patient.model_dump()
    mock_get.return_value = mock_response

    actual_bsn_scheme, actual_timestamp = metadata_service.get_update_scheme(DataDomain("ImagingStudy"))
    assert expected_bsn_scheme == actual_bsn_scheme
    assert expected_timestamp == actual_timestamp
    mock_get.assert_called_once()
