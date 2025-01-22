import logging
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Body, Depends
from fhir.resources.R4B.careplan import CarePlan
from fhir.resources.R4B.resource import Resource
from starlette.responses import Response

from app.config import get_config
from app.container import get_pseudonym_service, get_referral_service
from app.data import BSN, DataDomain, UraNumber, UziNumber
from app.exceptions.service_exceptions import InvalidResourceException
from app.services.cp_extractor import CarePlanExtractor
from app.services.pseudonym_service import PseudonymService
from app.services.referral_service import ReferralService

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/registration",
    tags=["Registration Service"],
)


def validate_careplan(resource: Dict[str, Any]) -> Tuple[Resource, DataDomain, BSN, UziNumber]:
    if "resourceType" not in resource:
        raise InvalidResourceException("Field 'resourceType' is missing in the request")

    careplan = CarePlan.parse_obj(resource)
    if careplan is None:
        raise InvalidResourceException("Resource is not a valid CarePlan")

    extractor = CarePlanExtractor(careplan)
    bsn = extractor.get_subject_bsn()
    uzi = extractor.get_author_uzi()

    return resource, DataDomain.CarePlan, bsn, uzi


@router.post("")
def create(
    request: Dict[str, Any] = Body(...),
    pseudonym_service: PseudonymService = Depends(get_pseudonym_service),
    referral_service: ReferralService = Depends(get_referral_service),
) -> Response:
    if request is None:
        logger.error("Resource is missing in the request")
        raise InvalidResourceException("Resource is missing in the request")

    (resource, data_domain, bsn, uzi) = validate_careplan(request)

    ura = UraNumber(get_config().app.ura_number)
    local_pseudonym = pseudonym_service.exchange_for_bsn(bsn)

    referral_service.create_referral(
        local_pseudonym,
        data_domain,
        ura,
        uzi,
    )
    return Response(status_code=201)
