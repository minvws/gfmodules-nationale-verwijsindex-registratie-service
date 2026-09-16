from pydantic import BaseModel


class DomainMapEntry(BaseModel):
    last_resource_update: str | None = None


DomainsMap = dict[str, DomainMapEntry]
