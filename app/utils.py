import json
from typing import Dict, List

from app.models.domains_map import DomainMapEntry, DomainsMap


def read_json(path: str) -> Dict[str, List[Dict[str, str]]]:
    with open(path) as f:
        data: Dict[str, List[Dict[str, str]]] = json.load(f)
        return data


def create_domains_map(path: str) -> DomainsMap:
    data = read_json(path)
    domains: DomainsMap = {}

    for key, value in data.items():
        domains[key] = [DomainMapEntry(**v) for v in value]

    return domains
