import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends
from fhir.resources.R4B.bundle import Bundle
from starlette.responses import JSONResponse, Response

from app.container import (
    get_bundle_registration_service,
)
from app.exceptions.service_exceptions import InvalidResourceException
from app.services.registration.bundle import BundleRegistartionService

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/registration",
    tags=["Registration Service"],
)


@router.post("", summary="Create Referral Registration", description="Register a referral through a FHIR bundle.")
def create(
    request: Dict[str, Any] | None = Body(...),
    bundle_registration_service: BundleRegistartionService = Depends(get_bundle_registration_service),
) -> Response:
    if request is None:
        logger.error("Resource is missing in the request")
        raise InvalidResourceException("Resource is missing in the request")

    bundle = Bundle.model_validate(request)
    results = bundle_registration_service.register(bundle)

    return JSONResponse(status_code=200, content=results.model_dump())
