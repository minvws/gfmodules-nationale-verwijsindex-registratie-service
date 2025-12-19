from pydantic import BaseModel

from app.models.bsn import BSN


class Pseudonym(BaseModel):
    pseudonym: str


class PseudonymCreateDto(BaseModel):
    bsn: BSN
    provider_id: str | None = None
