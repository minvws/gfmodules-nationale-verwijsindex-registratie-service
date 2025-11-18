from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError

from app.models.domains_map import DomainMapEntry
from app.models.pseudonym import Pseudonym
from app.models.referrals import Referral
from app.models.update_scheme import BsnUpdateScheme, UpdateScheme
from app.services.synchronization.synchronizer import Synchronizer

PATCHED_METADATA_API = "app.services.metadata.MetadataService"
PATCHED_NVI_API = "app.services.nvi.NviService"
PATCHED_PSEUDONYM_API = "app.services.pseudonym.PseudonymService"
PATCHED_SYNCHRONIZE = "app.services.synchronization.synchronizer.Synchronizer.synchronize"
PATCHED_SYNCHRONIZE_HEALTH = "app.services.synchronization.synchronizer.Synchronizer._healthcheck_apis"


@pytest.fixture
def mock_domain_map_entry() -> DomainMapEntry:
    return DomainMapEntry()


@pytest.fixture
def mock_domain_map_entry_with_timestamp(datetime_now: str) -> DomainMapEntry:
    return DomainMapEntry(last_resource_update=datetime_now)


@pytest.fixture
def mock_bsn_update_scheme(mock_bsn_number: str, mock_referral: Referral) -> BsnUpdateScheme:
    return BsnUpdateScheme(bsn=mock_bsn_number, referral=mock_referral)


@pytest.fixture
def mock_update_scheme(mock_bsn_update_scheme: BsnUpdateScheme, mock_domain_map_entry: DomainMapEntry) -> UpdateScheme:
    return UpdateScheme(updated_data=[mock_bsn_update_scheme], domain_entry=mock_domain_map_entry)


@pytest.fixture
def mock_update_scheme_with_new_timestamp(
    mock_bsn_update_scheme: BsnUpdateScheme,
    mock_domain_map_entry_with_timestamp: DomainMapEntry,
) -> tuple[list[str], str | None]:
    return (
        [mock_bsn_update_scheme.bsn],
        mock_domain_map_entry_with_timestamp.last_resource_update,
    )


@pytest.fixture
def mock_udpate_scheme_with_no_updates(
    mock_domain_map_entry: DomainMapEntry,
) -> UpdateScheme:
    return UpdateScheme(updated_data=[], domain_entry=mock_domain_map_entry)


@pytest.fixture
def mock_update_scheme_with_only_new_timestamp(
    mock_domain_map_entry_with_timestamp: DomainMapEntry,
) -> UpdateScheme:
    return UpdateScheme(
        updated_data=[],
        domain_entry=mock_domain_map_entry_with_timestamp,
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
    expected = {"nvi_api": True, "metadata_api": True, "pseudonym_api": True}

    actual = synchronizer._healthcheck_apis()

    assert expected == actual
    mock_pseudonym_call.assert_called_once()
    mock_nvi_call.assert_called_once()
    mock_metadata_call.assert_called_once()


def test_get_allowed_domains(
    synchronizer: Synchronizer,
    data_domains: list[str],
) -> None:
    expected = data_domains

    actual = synchronizer.get_allowed_domains()

    assert expected == actual


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(f"{PATCHED_PSEUDONYM_API}.submit")
@patch(f"{PATCHED_NVI_API}.submit")
@patch(f"{PATCHED_NVI_API}.get_referrals")
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_succeed_when_there_is_data_from_metadata(
    mock_healthcheck: MagicMock,
    mock_nvi_get_referrals: MagicMock,
    mock_nvi_register: MagicMock,
    mock_pseudonym_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_referral: Referral,
    mock_domain_map_entry: DomainMapEntry,
    mock_pseudonym: Pseudonym,
    mock_update_scheme: UpdateScheme,
    mock_bsn_number: str,
) -> None:
    mock_healthcheck.return_value = {
        "nvi_api": True,
        "metadata_api": True,
        "pseudonym_api": True,
    }
    mock_metadata_get_update_scheme.return_value = ([mock_bsn_number], None)
    mock_nvi_register.return_value = mock_referral
    mock_pseudonym_register.return_value = mock_pseudonym
    mock_nvi_get_referrals.return_value = None
    expected = mock_update_scheme

    actual = synchronizer.synchronize("ImagingStudy", mock_domain_map_entry)

    assert expected == actual
    mock_metadata_get_update_scheme.assert_called_once()
    mock_pseudonym_register.assert_called()
    mock_nvi_get_referrals.assert_called()
    mock_nvi_register.assert_called()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(f"{PATCHED_PSEUDONYM_API}.submit")
@patch(f"{PATCHED_NVI_API}.submit")
@patch(f"{PATCHED_NVI_API}.get_referrals")
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_succeed_and_update_timestamp_on_domain_entry_when_there_is_update_from_metadata(
    mock_healthcheck: MagicMock,
    mock_nvi_get_referrals: MagicMock,
    mock_nvi_register: MagicMock,
    mock_pseudonym_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_referral: Referral,
    mock_domain_map_entry_with_timestamp: DomainMapEntry,
    mock_pseudonym: Pseudonym,
    datetime_now: str,
    mock_bsn_number: str,
    mock_update_scheme_with_new_timestamp: tuple[list[str], str | None],
) -> None:
    mock_healthcheck.return_value = {
        "nvi_api": True,
        "metadata_api": True,
        "pseudonym_api": True,
    }
    mock_metadata_get_update_scheme.return_value = [mock_bsn_number], datetime_now
    mock_pseudonym_register.return_value = mock_pseudonym
    mock_nvi_get_referrals.return_value = None
    mock_nvi_register.return_value = mock_referral
    expected = UpdateScheme(
        updated_data=[
            BsnUpdateScheme(
                bsn=mock_update_scheme_with_new_timestamp[0][0],
                referral=Referral(
                    pseudonym="some_pseudonym",
                    data_domain="beeldbank",
                    ura_number="12345678",
                ),
            )
        ],
        domain_entry=DomainMapEntry(
            last_resource_update=mock_update_scheme_with_new_timestamp[1],
        ),
    )

    actual = synchronizer.synchronize("ImagingStudy", mock_domain_map_entry_with_timestamp)

    assert expected == actual
    assert expected.domain_entry.last_resource_update == actual.domain_entry.last_resource_update

    mock_metadata_get_update_scheme.assert_called()
    mock_nvi_register.assert_called()
    mock_nvi_get_referrals.assert_called()
    mock_pseudonym_register.assert_called()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(f"{PATCHED_PSEUDONYM_API}.submit")
@patch(f"{PATCHED_NVI_API}.submit")
@patch(f"{PATCHED_NVI_API}.get_referrals")
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_succeed_and_return_only_new_domain_entries_when_no_patients_are_updated_from_metadata(
    mock_healthcheck: MagicMock,
    mock_nvi_get_referrals: MagicMock,
    mock_nvi_register: MagicMock,
    mock_pseudonym_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_domain_map_entry_with_timestamp: DomainMapEntry,
    mock_update_scheme_with_only_new_timestamp: UpdateScheme,
    datetime_now: str,
) -> None:
    mock_healthcheck.return_value = {
        "nvi_api": True,
        "metadata_api": True,
        "pseudonym_api": True,
    }
    expected = mock_update_scheme_with_only_new_timestamp
    mock_metadata_get_update_scheme.return_value = [], datetime_now

    actual = synchronizer.synchronize("ImagingStudy", mock_domain_map_entry_with_timestamp)

    assert expected == actual

    mock_metadata_get_update_scheme.assert_called()
    mock_pseudonym_register.assert_not_called()
    mock_nvi_register.assert_not_called()
    mock_nvi_get_referrals.assert_not_called()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(f"{PATCHED_PSEUDONYM_API}.submit")
@patch(f"{PATCHED_NVI_API}.submit")
@patch(f"{PATCHED_NVI_API}.get_referrals")
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_syncrhonize_should_succeed_and_update_timestamp_when_referral_exists(
    mock_healthcheck: MagicMock,
    mock_nvi_get_referrals: MagicMock,
    mock_nvi_register: MagicMock,
    mock_pseudonym_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_referral: Referral,
    mock_domain_map_entry_with_timestamp: DomainMapEntry,
    mock_pseudonym: Pseudonym,
    mock_bsn_number: str,
    datetime_now: str,
    mock_update_scheme_with_only_new_timestamp: UpdateScheme,
) -> None:
    mock_healthcheck.return_value = {
        "nvi_api": True,
        "metadata_api": True,
        "pseudonym_api": True,
    }
    mock_metadata_get_update_scheme.return_value = [mock_bsn_number], datetime_now
    mock_nvi_get_referrals.return_value = mock_referral
    mock_pseudonym_register.return_value = mock_pseudonym
    expected = mock_update_scheme_with_only_new_timestamp

    actual = synchronizer.synchronize("ImagingStudy", mock_domain_map_entry_with_timestamp)

    assert expected == actual
    mock_metadata_get_update_scheme.assert_called()
    mock_pseudonym_register.assert_called()
    mock_nvi_get_referrals.assert_called()
    mock_nvi_register.assert_not_called()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(f"{PATCHED_PSEUDONYM_API}.submit")
@patch(f"{PATCHED_NVI_API}.submit")
@patch(f"{PATCHED_NVI_API}.get_referrals")
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_fail_when_nvi_is_unreachable(
    mock_healthcheck: MagicMock,
    mock_nvi_get_referrals: MagicMock,
    mock_nvi_register: MagicMock,
    mock_pseudonym_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_pseudonym: str,
    mock_domain_map_entry: DomainMapEntry,
    mock_update_scheme_with_new_timestamp: tuple[list[str], str | None],
) -> None:
    mock_healthcheck.return_value = {
        "nvi_api": True,
        "metadata_api": True,
        "pseudonym_api": True,
    }
    mock_metadata_get_update_scheme.return_value = mock_update_scheme_with_new_timestamp
    mock_nvi_get_referrals.side_effect = ConnectionError
    mock_nvi_register.side_effect = ConnectionError
    mock_pseudonym_register.return_value = mock_pseudonym

    with pytest.raises(ConnectionError):
        synchronizer.synchronize("ImagingStudy", mock_domain_map_entry)

    mock_metadata_get_update_scheme.assert_called_once()
    mock_pseudonym_register.assert_called()
    mock_nvi_get_referrals.assert_called_once()
    mock_nvi_register.assert_not_called()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(f"{PATCHED_PSEUDONYM_API}.submit")
@patch(f"{PATCHED_NVI_API}.submit")
@patch(f"{PATCHED_NVI_API}.get_referrals")
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_synchronize_should_fail_when_pseudonym_api_is_unreachable(
    mock_healthcheck: MagicMock,
    mock_nvi_get_referrals: MagicMock,
    mock_nvi_register: MagicMock,
    mock_pseudonym_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_domain_map_entry: DomainMapEntry,
    mock_bsn_number: str,
) -> None:
    mock_healthcheck.return_value = {
        "nvi_api": True,
        "metadata_api": True,
        "pseudonym_api": True,
    }
    mock_metadata_get_update_scheme.return_value = [mock_bsn_number], None
    mock_pseudonym_register.side_effect = ConnectionError

    with pytest.raises(ConnectionError):
        synchronizer.synchronize("ImagingStudy", mock_domain_map_entry)

    mock_metadata_get_update_scheme.assert_called_once()
    mock_pseudonym_register.assert_called_once()
    mock_nvi_get_referrals.assert_not_called()
    mock_nvi_register.assert_not_called()


@patch(f"{PATCHED_METADATA_API}.get_update_scheme")
@patch(f"{PATCHED_PSEUDONYM_API}.submit")
@patch(f"{PATCHED_NVI_API}.submit")
@patch(f"{PATCHED_NVI_API}.get_referrals")
@patch(PATCHED_SYNCHRONIZE_HEALTH)
def test_syncrhonize_should_fail_when_metadata_is_unreachable(
    mock_healthcheck: MagicMock,
    mock_nvi_get_referrals: MagicMock,
    mock_nvi_register: MagicMock,
    mock_pseudonym_register: MagicMock,
    mock_metadata_get_update_scheme: MagicMock,
    synchronizer: Synchronizer,
    mock_domain_map_entry: DomainMapEntry,
) -> None:
    mock_healthcheck.return_value = {
        "nvi_api": True,
        "metadata_api": True,
        "pseudonym_api": True,
    }
    mock_metadata_get_update_scheme.side_effect = ConnectionError

    with pytest.raises(ConnectionError):
        synchronizer.synchronize("ImagingStudy", mock_domain_map_entry)

    mock_metadata_get_update_scheme.assert_called_once()
    mock_nvi_register.assert_not_called()
    mock_nvi_get_referrals.assert_not_called()
    mock_pseudonym_register.assert_not_called()


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
def test_synchronize_should_fail_when_there_is_no_connection_established(
    mock_synchronize: MagicMock, synchronizer: Synchronizer
) -> None:
    mock_synchronize.side_effect = ConnectionError

    with pytest.raises(ConnectionError):
        synchronizer.synchronize_domain("ImagingStudy")

    mock_synchronize.assert_called()
