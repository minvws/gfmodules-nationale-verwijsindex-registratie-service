from typing import Dict, List

from app.models.domains_map import DomainMapEntry, DomainsMap


class DomainsMapService:
    def __init__(self, data_domains: List[str]) -> None:
        # self.__domain_map: dict[str, List[DomainMapEntry]] = {}
        self.__domain_map: Dict[str, List[DomainMapEntry]] = {
            k: [DomainMapEntry(resource_type=k)] for k in data_domains
        }

    def get_domains(self) -> List[str]:
        return [k for k in self.__domain_map.keys()]

    def get_entries(self, data_domain: str) -> List[DomainMapEntry]:
        if data_domain not in self.__domain_map.keys():
            self.__domain_map[data_domain] = [DomainMapEntry(resource_type=data_domain)]

        return self.__domain_map[data_domain]

    def clear_entries_timestamp(self, data_domain: str) -> Dict[str, List[DomainMapEntry]]:
        entries = self.get_entries(data_domain)
        self.__domain_map[data_domain] = [DomainMapEntry(resource_type=data_domain) for _ in entries]

        return self.__domain_map

    def clear_all_entries_timestamp(self) -> DomainsMap:
        [self.clear_entries_timestamp(domain) for domain in self.get_domains()]
        return self.__domain_map
