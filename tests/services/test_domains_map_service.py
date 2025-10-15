import copy
from datetime import datetime

import pytest

from app.models.data_domain import DataDomain
from app.services.domain_map_service import DomainsMapService


def test_get_domains_should_return_a_list(
    domains_map_service: DomainsMapService,
) -> None:
    expected = [domain for domain in DataDomain.get_all()]
    actual = domains_map_service.get_domains()

    assert isinstance(actual, list)
    assert expected == actual


def test_get_entries_should_return_a_list_of_entries_when_given_correct_domain_names(
    domains_map_service: DomainsMapService,
) -> None:
    for domain in DataDomain.get_all():
        entries = domains_map_service.get_entries(domain)
        assert isinstance(entries, list)
        for entry in entries:
            assert entry.resource_type == str(domain.to_fhir())


@pytest.mark.parametrize("domain", DataDomain.get_all())
def test_clear_entries_timestamp_should_succeed(domains_map_service: DomainsMapService, domain: DataDomain) -> None:
    original = copy.deepcopy(domains_map_service.get_entries(domain))
    for entry in domains_map_service.get_entries(domain):
        entry.last_resource_update = datetime.now().isoformat()

    domains_map_service.clear_entries_timestamp(domain)
    cleared = domains_map_service.get_entries(domain)

    # Expect new entries with same resource_type
    assert [e.resource_type for e in cleared] == [e.resource_type for e in original]


def test_clear_all_entries_timestamps_should_succeed(
    domains_map_service: DomainsMapService,
) -> None:
    domains_map_service.clear_all_entries_timestamp()
    for domain in domains_map_service.get_domains():
        entries = domains_map_service.get_entries(domain)
        for entry in entries:
            assert entry.last_resource_update is None
