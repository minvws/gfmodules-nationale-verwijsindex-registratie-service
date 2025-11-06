import logging
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Body, Depends
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.careplan import CarePlan
from starlette.responses import JSONResponse, Response

from app.container import (
    get_bundle_registration_service,
)
from app.data import BSN
from app.exceptions.service_exceptions import InvalidResourceException
from app.services.cp_extractor import CarePlanExtractor
from app.services.registration.bundle import BundleRegistartionService

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/registration",
    tags=["Registration Service"],
)


def validate_careplan(resource: Dict[str, Any]) -> Tuple[str, BSN]:
    if not resource:
        raise InvalidResourceException("Resource is not a valid CarePlan")
    careplan = CarePlan(**resource)

    extractor = CarePlanExtractor(careplan)
    bsn = extractor.get_subject_bsn()

    return "CarePlan", bsn


@router.post("", description="Register a referral through a FHIR CarePlan resource")
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
