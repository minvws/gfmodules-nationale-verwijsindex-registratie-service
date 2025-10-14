import logging
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Body, Depends
from fhir.resources.R4B.careplan import CarePlan
from starlette.responses import Response

from app.container import get_nvi_service, get_pseudonym_service, get_ura_number
from app.data import BSN, DataDomain
from app.exceptions.service_exceptions import InvalidResourceException
from app.models.pseudonym import PseudonymCreateDto
from app.models.referrals import CreateReferralDTO
from app.models.ura_number import UraNumber
from app.services.cp_extractor import CarePlanExtractor
from app.services.nvi import NviService
from app.services.pseudonym import PseudonymService

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
    pseudonym_api_service: PseudonymService = Depends(get_pseudonym_service),
    nvi_api_service: NviService = Depends(get_nvi_service),
    ura_number: UraNumber = Depends(get_ura_number),
) -> Response:
    if request is None:
        logger.error("Resource is missing in the request")
        raise InvalidResourceException("Resource is missing in the request")

    (data_domain, bsn) = validate_careplan(request)

    local_pseudonym = pseudonym_api_service.submit(PseudonymCreateDto(bsn=BSN(bsn)))

    create_referral_dto = CreateReferralDTO(
        ura_number=ura_number.value,
        requesting_uzi_number=ura_number.value,
        pseudonym=str(local_pseudonym.pseudonym),
        data_domain=data_domain.value,
    )
    nvi_api_service.submit(create_referral_dto)

    return Response(status_code=201)
