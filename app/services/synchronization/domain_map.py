from typing import List

from app.models.data_domain import DataDomain
from app.models.domains_map import DomainMapEntry, DomainsMap


class DomainsMapService:
    def __init__(self, data_domains: List[DataDomain]) -> None:
        self.__domain_map: DomainsMap = {k: DomainMapEntry() for k in data_domains}

    def get_domains(self) -> List[DataDomain]:
        return list(self.__domain_map.keys())

    def get_entry(self, data_domain: DataDomain) -> DomainMapEntry:
        if data_domain not in self.get_domains():
            raise KeyError(f"{data_domain} is not known to defined list of DataDomains.")

        return self.__domain_map[data_domain]

    def clear_entry_timestamp(self, data_domain: DataDomain) -> DomainsMap:
        if data_domain not in self.get_domains():
            raise KeyError(f"{data_domain} is not known to defined list of DataDomains.")

        self.__domain_map[data_domain] = DomainMapEntry()
        return self.__domain_map

    def clear_all_entries_timestamp(self) -> DomainsMap:
        self.__domain_map = {k: DomainMapEntry() for k in self.get_domains()}
        return self.__domain_map
