from typing import Any, Dict

from fastapi import Body
from pydantic import BaseModel, field_validator

from app.data import BSN, UraNumber


class RegistrationRequest(BaseModel):
    ura: UraNumber
    bsn: BSN
    resource: Dict[str, Any] = Body(...)

    @field_validator("ura", mode="before")
    def validate_ura(cls, ura: str) -> UraNumber:
        return UraNumber(ura)

    @field_validator("bsn", mode="before")
    def validate_bsn(cls, bsn: str) -> BSN:
        return BSN(bsn)
