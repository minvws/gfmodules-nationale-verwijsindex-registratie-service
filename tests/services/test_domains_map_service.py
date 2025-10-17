import copy
from datetime import datetime
from typing import List

from app.services.domain_map_service import DomainsMapService


def test_get_domains_should_return_a_list(domains_map_service: DomainsMapService, data_domains: List[str]) -> None:
    expected = data_domains
    actual = domains_map_service.get_domains()

    assert isinstance(actual, list)
    assert expected == actual


def test_get_entries_should_return_a_list_of_entries_when_given_correct_domain_names(
    domains_map_service: DomainsMapService, data_domains: List[str]
) -> None:
    for domain in data_domains:
        entries = domains_map_service.get_entries(domain)
        assert isinstance(entries, list)
        for entry in entries:
            assert entry.resource_type == domain


def test_cear_entries_timestanp_should_succeed(
    domains_map_service: DomainsMapService,
) -> None:
    original = copy.deepcopy(domains_map_service.get_entries("ImagingStudy"))
    for entry in domains_map_service.get_entries("ImaginStudy"):
        entry.last_resource_update = datetime.now().isoformat()

    domains_map_service.clear_entries_timestamp("ImagingStudy")
    cleared = domains_map_service.get_entries("ImagingStudy")

    assert [e.last_resource_update for e in cleared] == [e.last_resource_update for e in original]


def test_clear_all_entries_timestamps_should_succeed(
    domains_map_service: DomainsMapService,
) -> None:
    domains_map_service.clear_all_entries_timestamp()
    for domain in domains_map_service.get_domains():
        entries = domains_map_service.get_entries(domain)
        for entry in entries:
            assert entry.last_resource_update is None
