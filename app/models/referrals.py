from pydantic import BaseModel


class Referral(BaseModel):
    pseudonym: str
    data_domain: str
    ura_number: str


class ReferralQueryDTO(Referral):
    pass


class CreateRefferalDTO(Referral):
    requesting_uzi_number: str
