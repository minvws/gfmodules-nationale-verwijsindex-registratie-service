from typing import Dict

from pydantic import BaseModel

from app.models.data_domain import DataDomain


class DomainMapEntry(BaseModel):
    last_resource_update: str | None = None


DomainsMap = Dict[DataDomain, DomainMapEntry]
