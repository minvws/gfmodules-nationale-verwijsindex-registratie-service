from typing import Annotated, List

from fastapi import APIRouter, Depends

from app.container import get_referral_registration_service
from app.models.referrals import Referral
from app.services.registration.referrals import ReferralRegistrationService


test_router = APIRouter(
    prefix="/test",
    tags=["Test Service"],
)


@test_router.get(
    "/register",
    summary="Register referrals for a BSN",
)
def register_referrals(
    bsn: str,
    referral_registration_service: Annotated[ReferralRegistrationService, Depends(get_referral_registration_service)],
) -> Referral | None:
    return referral_registration_service.register(bsn)


@test_router.get(
    "/query",
    summary="Query referrals for a BSN",
)
def query_referrals(
    bsn: str,
    referral_registration_service: Annotated[ReferralRegistrationService, Depends(get_referral_registration_service)],
) -> List[Referral]:
    return referral_registration_service.query(bsn)


@test_router.get(
    "/localize",
    summary="Localize referrals for a BSN",
)
def localize_referrals(
    bsn: str,
    referral_registration_service: Annotated[ReferralRegistrationService, Depends(get_referral_registration_service)],
) -> List[Referral]:
    return referral_registration_service.localize(bsn)
