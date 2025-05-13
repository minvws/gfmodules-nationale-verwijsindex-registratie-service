from typing import Dict, List

from pydantic import BaseModel


class DomainMapEntry(BaseModel):
    resource_type: str
    last_resource_update: str | None = None


DomainsMap = Dict[str, List[DomainMapEntry]]
