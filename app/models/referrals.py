from pydantic import BaseModel

from app.models.data_domain import DataDomain
from app.models.ura_number import UraNumber


class ReferralRequest(BaseModel):
    oprf_jwe: str
    blind_factor: str
    data_domain: DataDomain


class CreateReferralRequest(ReferralRequest):
    ura_number: UraNumber
    requesting_uzi_number: str
    organization_type: str

class ReferralQuery(BaseModel):
    oprf_jwe: str | None = None
    blind_factor: str | None = None
    data_domain: DataDomain | None = None
    ura_number: UraNumber


class ReferralEntity(BaseModel):
    ura_number: UraNumber
    pseudonym: str
    data_domain: DataDomain
    organization_type: str
