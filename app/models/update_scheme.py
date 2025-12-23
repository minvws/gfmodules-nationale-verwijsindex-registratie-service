from typing import List

from pydantic import BaseModel

from app.models.domains_map import DomainMapEntry
from app.models.referrals import ReferralEntity


class BsnUpdateScheme(BaseModel):
    bsn: str
    referral: ReferralEntity


class UpdateScheme(BaseModel):
    updated_data: List[BsnUpdateScheme]
    domain_entry: DomainMapEntry
