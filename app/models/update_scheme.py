from typing import List

from pydantic import BaseModel

from app.models.domains_map import DomainMapEntry
from app.models.referrals import Referral


class BsnUpdateScheme(BaseModel):
    bsn: str
    referral: Referral


class UpdateScheme(BaseModel):
    updated_data: List[BsnUpdateScheme]
    domain_entry: DomainMapEntry
