import copy
from datetime import datetime
from typing import List

import pytest

from app.models.data_domain import DataDomain
from app.models.domains_map import DomainMapEntry
from app.services.synchronization.domain_map import DomainsMapService


def test_get_domains_should_return_a_list(domains_map_service: DomainsMapService, data_domains: List[DataDomain]) -> None:
    expected = data_domains
    actual = domains_map_service.get_domains()

    assert isinstance(actual, list)
    assert expected == actual


def test_get_entry_should_return_an_entry_when_given_correct_domain(
    domains_map_service: DomainsMapService, data_domains: List[DataDomain]
) -> None:
    for domain in data_domains:
        entry = domains_map_service.get_entry(domain)
        assert isinstance(entry, DomainMapEntry)
        assert entry.last_resource_update is None


def test_get_entry_should_raise_exception_when_given_unknown_data_domain(
    domains_map_service: DomainsMapService,
) -> None:
    with pytest.raises(KeyError):
        domains_map_service.get_entry(DataDomain("SomeDomain"))


def test_clear_entry_timestamp_should_succeed(domains_map_service: DomainsMapService, data_domains: List[DataDomain]) -> None:
    for data_domain in data_domains:
        actual_entry = copy.deepcopy(domains_map_service.get_entry(data_domain))

        entry = domains_map_service.get_entry(data_domain)
        entry.last_resource_update = datetime.now().isoformat()
        assert entry.last_resource_update is not None

        domains_map_service.clear_entry_timestamp(data_domain)
        expected = domains_map_service.get_entry(data_domain)

        assert expected.last_resource_update == actual_entry.last_resource_update


def test_clear_entry_timestamp_should_raise_exception_when_given_unknown_data_domain(
    domains_map_service: DomainsMapService,
) -> None:
    with pytest.raises(KeyError):
        domains_map_service.clear_entry_timestamp(DataDomain("SomeDomain"))


def test_clear_all_entries_timestamps_should_succeed(
    domains_map_service: DomainsMapService, data_domains: List[DataDomain]
) -> None:
    for data_domain in data_domains:
        entry = domains_map_service.get_entry(data_domain)
        entry.last_resource_update = datetime.now().isoformat()

    domains_map_service.clear_all_entries_timestamp()
    for data_domain in data_domains:
        entry = domains_map_service.get_entry(data_domain)
        assert entry.last_resource_update is None
