from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError

from app.models.domains_map import DomainMapEntry
from app.models.referrals import Referral
from app.models.update_scheme import BsnUpdateScheme, UpdateScheme
from app.services.synchronization.synchronizer import Synchronizer

PATCHED_METADATA_API = "app.services.metadata.MetadataService"
PATCHED_NVI_API = "app.services.nvi.NviService"
PATCHED_PSEUDONYM_API = "app.services.pseudonym.PseudonymService"
PATCHED_REGISTER = "app.services.registration.referrals.ReferralRegistrationService.register"
PATCHED_SYNCHRONIZE = "app.services.synchronization.synchronizer.Synchronizer.synchronize"
PATCHED_SYNCHRONIZE_HEALTH = "app.services.synchronization.synchronizer.Synchronizer._healthcheck_apis"

HEALTHY = {"nvi_api": True, "metadata_api": True, "pseudonym_api": True}


@pytest.fixture
def mock_domain_map_entry() -> DomainMapEntry:
    return DomainMapEntry()


@pytest.fixture
def mock_domain_map_entry_with_timestamp(datetime_now: str) -> DomainMapEntry:
    return DomainMapEntry(last_resource_update=datetime_now)


@pytest.fixture
def mock_update_scheme(mock_bsn_number: str, mock_referral: Referral) -> UpdateScheme:
    return UpdateScheme(
        updated_data=[BsnUpdateScheme(bsn=mock_bsn_number, referral=mock_referral)],
        domain_entry=DomainMapEntry(),
    )


@patch(f"{PATCHED_METADATA_API}.server_healthy", return_value=True)
@patch(f"{PATCHED_NVI_API}.server_healthy", return_value=True)
@patch(f"{PATCHED_PSEUDONYM_API}.server_healthy", return_value=True)
def test_healthcheck_apis_should_succeed(
    mock_pseudonym_call: MagicMock,
    mock_nvi_call: MagicMock,
    mock_metadata_call: MagicMock,
    synchronizer: Synchronizer,
) -> None:
    actual = synchronizer._healthcheck_apis()

    assert actual == HEALTHY
    mock_pseudonym_call.assert_called_once()
    mock_nvi_call.assert_called_once()
    mock_metadata_call.assert_called_once()


def test_get_allowed_domains(
    synchronizer: Synchronizer,
    data_domains: list[str],
) -> None:
    assert synchronizer.get_allowed_domains() == data_domains


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(PATCHED_REGISTER)
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_succeed_when_there_is_data_from_metadata(
    mock_healthcheck: MagicMock,
    mock_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_referral: Referral,
    mock_domain_map_entry: DomainMapEntry,
    mock_update_scheme: UpdateScheme,
    mock_bsn_number: str,
) -> None:
    mock_healthcheck.return_value = HEALTHY
    mock_metadata_get_update_scheme.return_value = ([mock_bsn_number], None)
    mock_register.return_value = mock_referral

    actual = synchronizer.synchronize("ImagingStudy", mock_domain_map_entry)

    assert actual == mock_update_scheme
    mock_metadata_get_update_scheme.assert_called_once()
    mock_register.assert_called_once()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(PATCHED_REGISTER)
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_update_timestamp_when_metadata_has_newer_timestamp(
    mock_healthcheck: MagicMock,
    mock_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_referral: Referral,
    mock_domain_map_entry: DomainMapEntry,
    datetime_now: str,
    mock_bsn_number: str,
) -> None:
    mock_healthcheck.return_value = HEALTHY
    mock_metadata_get_update_scheme.return_value = ([mock_bsn_number], datetime_now)
    mock_register.return_value = mock_referral

    actual = synchronizer.synchronize("ImagingStudy", mock_domain_map_entry)

    assert actual.domain_entry.last_resource_update == datetime_now
    mock_register.assert_called_once()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(PATCHED_REGISTER)
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_return_no_updates_when_no_patients_from_metadata(
    mock_healthcheck: MagicMock,
    mock_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_domain_map_entry_with_timestamp: DomainMapEntry,
    datetime_now: str,
) -> None:
    mock_healthcheck.return_value = HEALTHY
    mock_metadata_get_update_scheme.return_value = ([], datetime_now)

    actual = synchronizer.synchronize("ImagingStudy", mock_domain_map_entry_with_timestamp)

    assert actual.updated_data == []
    mock_register.assert_not_called()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(PATCHED_REGISTER)
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_skip_when_referral_already_exists(
    mock_healthcheck: MagicMock,
    mock_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_domain_map_entry: DomainMapEntry,
    mock_bsn_number: str,
    datetime_now: str,
) -> None:
    mock_healthcheck.return_value = HEALTHY
    mock_metadata_get_update_scheme.return_value = ([mock_bsn_number], datetime_now)
    mock_register.return_value = None

    actual = synchronizer.synchronize("ImagingStudy", mock_domain_map_entry)

    assert actual.updated_data == []
    mock_register.assert_called_once()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(PATCHED_REGISTER)
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_fail_when_registration_is_unreachable(
    mock_healthcheck: MagicMock,
    mock_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_domain_map_entry: DomainMapEntry,
    mock_bsn_number: str,
) -> None:
    mock_healthcheck.return_value = HEALTHY
    mock_metadata_get_update_scheme.return_value = ([mock_bsn_number], None)
    mock_register.side_effect = ConnectionError

    with pytest.raises(ConnectionError):
        synchronizer.synchronize("ImagingStudy", mock_domain_map_entry)

    mock_register.assert_called_once()


@patch(PATCHED_SYNCHRONIZE)
def test_synchronize_domain_should_succeed_when_there_is_data_to_update(
    mock_synchronize: MagicMock,
    synchronizer: Synchronizer,
    mock_update_scheme: UpdateScheme,
) -> None:
    mock_synchronize.return_value = mock_update_scheme
    expected = {"ImagingStudy": [mock_update_scheme]}

    actual = synchronizer.synchronize_domain("ImagingStudy")

    assert expected == actual
    mock_synchronize.assert_called()


@patch(PATCHED_SYNCHRONIZE)
def test_synchronize_domain_should_fail_when_there_is_no_connection_established(
    mock_synchronize: MagicMock, synchronizer: Synchronizer
) -> None:
    mock_synchronize.side_effect = ConnectionError

    with pytest.raises(ConnectionError):
        synchronizer.synchronize_domain("ImagingStudy")

    mock_synchronize.assert_called()
