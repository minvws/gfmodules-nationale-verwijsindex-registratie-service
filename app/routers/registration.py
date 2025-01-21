import logging
from typing import Tuple, Dict, Any

from fastapi import APIRouter, Depends
from fhir.resources.R4B.careplan import CarePlan
from fhir.resources.R4B.resource import Resource
from starlette.responses import Response

from app.config import get_config
from app.container import get_pseudonym_service, get_referral_service
from app.data import DataDomain
from app.exceptions.service_exceptions import InvalidResourceException
from app.params.registration_request import RegistrationRequest
from app.services.pseudonym_service import PseudonymService
from app.services.referral_service import ReferralService

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/registration",
    tags=["Registration Service"],
)

def validate_resource(resource: Dict[str, Any]) -> Tuple[Resource, DataDomain]:
    """
    Extracts the resource and data domain from the resource. Raises an exception
    when the resource if not a valid resource.
    """
    if "resourceType" not in resource:
        raise InvalidResourceException("Field 'resourceType' is missing in the request")

    resource_type = resource["resourceType"].lower()
    if resource_type == "careplan":
        resource = CarePlan.parse_obj(resource)
        if resource is None:
            raise InvalidResourceException("Resource is not a valid CarePlan")

        return resource, DataDomain.CarePlan
    else:
        raise InvalidResourceException("Resource type is not a CarePlan")


@router.post("")
def create(
    request: RegistrationRequest,
    pseudonym_service: PseudonymService = Depends(get_pseudonym_service),
    referral_service: ReferralService = Depends(get_referral_service)
) -> Response:
    if request.resource is None:
        logger.error("Resource is missing in the request")
        raise InvalidResourceException("Resource is missing in the request")

    (resource, data_domain) = validate_resource(request.resource)

    requesting_uzi_number = get_config().app.uzi_number
    local_pseudonym = pseudonym_service.exchange_for_bsn(request.bsn)

    referral_service.create_referral(
        local_pseudonym,
        data_domain,
        request.ura,
        requesting_uzi_number,
    )
    return Response(status_code=201)
