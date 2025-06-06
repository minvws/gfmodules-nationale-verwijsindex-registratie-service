import logging
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Body, Depends
from fhir.resources.R4B.careplan import CarePlan
from starlette.responses import Response

from app.config import get_config
from app.container import get_nvi_api_service, get_pseudonym_api_service
from app.data import BSN, DataDomain
from app.exceptions.service_exceptions import InvalidResourceException
from app.models.pseudonym import PseudonymCreateDto
from app.models.referrals import CreateReferralDTO
from app.services.api.nvi_api_service import NviApiService
from app.services.api.pseudonym_api_service import PseudonymApiService
from app.services.cp_extractor import CarePlanExtractor

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/registration",
    tags=["Registration Service"],
)


def validate_careplan(resource: Dict[str, Any]) -> Tuple[DataDomain, BSN]:
    if not resource:
        raise InvalidResourceException("Resource is not a valid CarePlan")
    careplan = CarePlan(**resource)

    extractor = CarePlanExtractor(careplan)
    bsn = extractor.get_subject_bsn()

    return DataDomain.CarePlan, bsn


@router.post("", description="Register a referral through a FHIR CarePlan resource")
def create(
    request: Dict[str, Any] | None = Body(...),
    pseudonym_api_service: PseudonymApiService = Depends(get_pseudonym_api_service),
    nvi_api_service: NviApiService = Depends(get_nvi_api_service),
) -> Response:
    if request is None:
        logger.error("Resource is missing in the request")
        raise InvalidResourceException("Resource is missing in the request")

    (data_domain, bsn) = validate_careplan(request)

    local_pseudonym = pseudonym_api_service.submit(PseudonymCreateDto(bsn=BSN(bsn)))

    create_referral_dto = CreateReferralDTO(
        ura_number=get_config().app.ura_number,
        requesting_uzi_number=get_config().app.ura_number,
        pseudonym=str(local_pseudonym.pseudonym),
        data_domain=data_domain.value,
    )
    nvi_api_service.submit(create_referral_dto)

    return Response(status_code=201)
