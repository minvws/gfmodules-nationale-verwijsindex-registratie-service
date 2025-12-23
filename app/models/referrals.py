from pydantic import BaseModel, Field, field_serializer, model_validator
from app.models.data_domain import DataDomain
from app.models.pseudonym import OprfPseudonymJWE
from app.models.ura_number import UraNumber


class CreateReferralRequest(BaseModel):
    oprf_jwe: OprfPseudonymJWE = Field(serialization_alias="pseudonym")
    blind_factor: str = Field(serialization_alias="oprfKey")
    ura_number: UraNumber = Field(serialization_alias="source")
    organization_type: str = Field(serialization_alias="sourceType")
    data_domain: DataDomain = Field(serialization_alias="careContext")

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
    oprf_jwe: OprfPseudonymJWE | None = Field(serialization_alias="pseudonym", default=None)
    blind_factor: str | None = Field(serialization_alias="oprfKey", default=None)
    data_domain: DataDomain | None = Field(serialization_alias="careContext", default=None)
    ura_number: UraNumber = Field(serialization_alias="source")

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
