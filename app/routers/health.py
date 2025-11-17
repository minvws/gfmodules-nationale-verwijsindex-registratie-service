import logging
from typing import Any

from fastapi import APIRouter, Depends

from app import container
from app.services.metadata import MetadataService
from app.services.nvi import NviService
from app.services.OtvService.otv_stub_service import OtvStubService
from app.services.pseudonym import PseudonymService

logger = logging.getLogger(__name__)
router = APIRouter()


def ok_or_error(value: bool) -> str:
    return "ok" if value else "error"


@router.get("/health", description="Health check for the API services")
def health(
    pseudonym_service: PseudonymService = Depends(container.get_pseudonym_service),
    referral_service: NviService = Depends(container.get_nvi_service),
    metadata_service: MetadataService = Depends(container.get_metadata_service),
    otv_stub_service: OtvStubService = Depends(container.get_otv_service),
) -> dict[str, Any]:
    components = {
        "pseudonym_service": ok_or_error(pseudonym_service.server_healthy()),
        "referral_service": ok_or_error(referral_service.server_healthy()),
        "metadata_api": ok_or_error(metadata_service.server_healthy()),
        "otv_stub_service": ok_or_error(otv_stub_service.server_healthy()),
    }
    healthy = ok_or_error(all(value == "ok" for value in components.values()))

    return {"status": healthy, "components": components}
