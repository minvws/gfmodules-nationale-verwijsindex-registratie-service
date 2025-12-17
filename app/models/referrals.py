from app.models.pseudonym import OprfPseudonymJWE, Pseudonym


class Referral(Pseudonym):
    data_domain: str
    ura_number: str


class ReferralQueryDTO(Referral):
    pass


class CreateReferralDTO(Referral):
    requesting_uzi_number: str
    encrypted_lmr_id: str
    oprf_blinded_jwe: OprfPseudonymJWE
    oprf_blind: str
