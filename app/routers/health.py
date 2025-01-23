import logging
from typing import Any

from fastapi import APIRouter, Depends

from app import container
from app.services.pseudonym_service import PseudonymService
from app.services.referral_service import ReferralService

logger = logging.getLogger(__name__)
router = APIRouter()


def ok_or_error(value: bool) -> str:
    return "ok" if value else "error"


@router.get("/health")
def health(
    pseudonym_service: PseudonymService = Depends(container.get_pseudonym_service),
    referral_service: ReferralService = Depends(container.get_referral_service),
) -> dict[str, Any]:
    components = {
        "pseudonym_service": ok_or_error(pseudonym_service.is_healthy()),
        "referral_service": ok_or_error(referral_service.is_healthy()),
    }
    healthy = ok_or_error(all(value == "ok" for value in components.values()))

    return {"status": healthy, "components": components}
