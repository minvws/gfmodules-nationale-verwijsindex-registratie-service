from typing import Dict, List

from app.models.data_domain import DataDomain
from app.models.domains_map import DomainMapEntry, DomainsMap


class DomainsMapService:
    def __init__(self) -> None:
        self.__domain_map: dict[str, List[DomainMapEntry]] = {}

    def get_domains(self) -> List["DataDomain"]:
        return DataDomain.get_all()

    def get_entries(self, data_domain: DataDomain) -> List[DomainMapEntry]:
        if str(data_domain.to_fhir()) not in self.__domain_map:
            self.__domain_map[str(data_domain.to_fhir())] = [DomainMapEntry(resource_type=str(data_domain.to_fhir()))]
        return self.__domain_map[str(data_domain.to_fhir())]

    def clear_entries_timestamp(self, data_domain: DataDomain) -> Dict[str, List[DomainMapEntry]]:
        entries = self.get_entries(data_domain)
        self.__domain_map[str(data_domain.to_fhir())] = [
            DomainMapEntry(resource_type=str(data_domain.to_fhir())) for entry in entries
        ]
        return self.__domain_map

    def clear_all_entries_timestamp(self) -> DomainsMap:
        [self.clear_entries_timestamp(domain) for domain in self.get_domains()]
        return self.__domain_map
