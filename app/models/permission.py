from typing import Any

from pydantic import BaseModel, model_validator

from app.models.pseudonym import Pseudonym as PseudonymModel
from app.models.ura_number import UraNumber


class OtvStubResourceDto(BaseModel):
    pseudonym: str
    org_ura: str
    org_category: str


class OtvStubSubjectDto(BaseModel):
    org_ura: str


class OtvStubDto(BaseModel):
    resource: OtvStubResourceDto
    subject: OtvStubSubjectDto


class OtvStubPermissionRequest(BaseModel):
    reversible_pseudonym: PseudonymModel
    client_ura_number: UraNumber


class PermissionRequestModel(BaseModel):
    encrypted_lmr_id: str
    client_ura_number: Any

    @model_validator(mode="after")
    def parse_ura_number(self) -> "PermissionRequestModel":
        if isinstance(self.client_ura_number, UraNumber):
            return self
        value = str(self.client_ura_number)
        self.client_ura_number = UraNumber(value)
        return self
