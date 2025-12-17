from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Pseudonym(BaseModel):
    pseudonym: str


class PseudonymRequest(BaseModel):
    encrypted_personal_id: str
    recipient_organization: str
    recipient_scope: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

class OprfPseudonymJWE(BaseModel):
    jwe: str = Field(min_length=1)


class PersonalIdentifier(BaseModel):
    """
    Model representing a personal identifier used in OPRF operations.
    """

    land_code: str
    type: str
    value: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
