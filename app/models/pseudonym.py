from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.bsn import BSN


class Pseudonym(BaseModel):
    pseudonym: str


class PseudonymCreateDto(BaseModel):
    bsn: BSN
    provider_id: str | None = None


class ReversiblePseudonymRequest(BaseModel):
    personal_id: str
    recipient_organization: str
    recipient_scope: str
    pseudonym_type: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
