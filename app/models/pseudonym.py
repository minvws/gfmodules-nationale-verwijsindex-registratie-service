from pydantic import BaseModel


class Pseudonym(BaseModel):
    pseudonym: str


class PseudonymCreateDto(BaseModel):
    bsn: str
    provider_id: str
