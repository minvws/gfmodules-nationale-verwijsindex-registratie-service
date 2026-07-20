from uuid import UUID
from pydantic import BaseModel


class Referral(BaseModel):
    id: UUID
    ura_number: str
    source_id: str | None
