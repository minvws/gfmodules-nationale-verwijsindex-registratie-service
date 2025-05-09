from typing import Dict, List

from app.models.domains_map import DomainMapEntry, DomainsMap


class DomainsMapService:
    def __init__(self, domains_map: DomainsMap) -> None:
        self.__domain_map = domains_map

    def get_domains(self) -> List[str]:
        return list(self.__domain_map.keys())

    def get_entries(self, data_domain: str) -> List[DomainMapEntry]:
        self.__validate_data_domain(data_domain)
        return self.__domain_map[data_domain]

    def clear_entries_timestamp(self, data_domain: str) -> Dict[str, List[DomainMapEntry]]:
        self.__validate_data_domain(data_domain)
        entries = self.get_entries(data_domain)
        self.__domain_map[data_domain] = [DomainMapEntry(resource_type=entry.resource_type) for entry in entries]
        return self.__domain_map

    def clear_all_entries_timepstam(self) -> DomainsMap:
        [self.clear_entries_timestamp(domain) for domain in self.get_domains()]
        return self.__domain_map

    def __validate_data_domain(self, data_domain: str) -> None:
        if data_domain not in self.get_domains():
            raise ValueError(f"Invalid {data_domain}, check value or update domains_map.json file")
