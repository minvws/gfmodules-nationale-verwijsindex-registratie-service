import logging
from typing import Any

from fastapi import APIRouter, Depends

from app import container
from app.services.api.metadata_api_service import MetadataApiService
from app.services.api.nvi_api_service import NviApiService
from app.services.api.pseudonym_api_service import PseudonymApiService

logger = logging.getLogger(__name__)
router = APIRouter()


def ok_or_error(value: bool) -> str:
    return "ok" if value else "error"


@router.get("/health", description="Health check for the API services")
def health(
    pseudonym_service: PseudonymApiService = Depends(container.get_pseudonym_api_service),
    referral_service: NviApiService = Depends(container.get_nvi_api_service),
    metadata_service: MetadataApiService = Depends(container.get_metadata_api_service),
) -> dict[str, Any]:
    components = {
        "pseudonym_service": ok_or_error(pseudonym_service.api_healthy()),
        "referral_service": ok_or_error(referral_service.api_healthy()),
        "metadata_api": ok_or_error(metadata_service.api_healthy()),
    }
    healthy = ok_or_error(all(value == "ok" for value in components.values()))

    return {"status": healthy, "components": components}
