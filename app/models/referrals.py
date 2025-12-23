from pydantic import BaseModel, field_serializer, model_validator
from app.models.data_domain import DataDomain
from app.models.pseudonym import OprfPseudonymJWE
from app.models.ura_number import UraNumber


class CreateReferralRequest(BaseModel):
    oprf_jwe: OprfPseudonymJWE
    blind_factor: str
    ura_number: UraNumber
    organization_type: str
    data_domain: DataDomain
    requesting_uzi_number: str

    @field_serializer("data_domain", when_used="json")
    def serialize_data_domain(self, data_domain: DataDomain) -> str:
        return str(data_domain.value)

    @field_serializer("ura_number", when_used="json")
    def serialize_ura_number(self, ura_number: UraNumber) -> str:
        return str(ura_number.value)

    @field_serializer("oprf_jwe", when_used="json")
    def serialize_oprf_jwe(self, oprf_jwe: OprfPseudonymJWE) -> str:
        return str(oprf_jwe.jwe)


class ReferralQuery(BaseModel):
    oprf_jwe: OprfPseudonymJWE | None = None
    blind_factor: str | None = None
    data_domain: DataDomain | None = None
    ura_number: UraNumber

    @field_serializer("data_domain", when_used="json")
    def serialize_data_domain(self, data_domain: DataDomain | None) -> str | None:
        return str(data_domain.value) if data_domain else None

    @field_serializer("ura_number", when_used="json")
    def serialize_ura_number(self, ura_number: UraNumber) -> str:
        return str(ura_number.value)

    @field_serializer("oprf_jwe", when_used="json")
    def serialize_oprf_jwe(self, oprf_jwe: OprfPseudonymJWE | None) -> str | None:
        return str(oprf_jwe.jwe) if oprf_jwe else None

    @model_validator(mode="after")
    def both_or_none(self) -> "ReferralQuery":
        if (self.oprf_jwe is None) != (self.blind_factor is None):
            raise ValueError("Both oprf_jwe and blind_factor must be provided or both must be None")
        return self


class ReferralEntity(BaseModel):
    ura_number: UraNumber
    pseudonym: str
    data_domain: DataDomain
    organization_type: str | None = None
