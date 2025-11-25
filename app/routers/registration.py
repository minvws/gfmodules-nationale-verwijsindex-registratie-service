import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, status
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


@router.post(
    "",
    summary="Create Referral Registration",
    description="""Register a referral through a FHIR R4B bundle.
    
    This endpoint processes FHIR R4B Bundle resources containing referral information.
    The bundle should include all necessary resources for registering a patient referral
    in the National Referral Index (NVI).
    
    **Request Requirements:**
    - Must be a valid FHIR R4B Bundle resource
    - Bundle type should be appropriate for transaction/batch processing
    - Should contain referral-related resources (Patient, ServiceRequest, etc.)
    
    **Processing:**
    - Validates the FHIR bundle structure
    - Extracts referral information
    - Performs pseudonymization if required
    - Registers the referral in the NVI system
    - Returns a response bundle with operation outcomes
    """,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Referral registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "resourceType": "Bundle",
                        "type": "transaction-response",
                        "entry": [
                            {
                                "response": {
                                    "status": "201 Created",
                                    "location": "ServiceRequest/example-id"
                                }
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Invalid FHIR bundle or missing required resources",
            "content": {
                "application/json": {
                    "example": {"detail": "Resource is missing in the request"}
                }
            }
        },
        422: {
            "description": "Validation error - bundle structure is invalid"
        },
        500: {
            "description": "Internal server error during registration"
        }
    }
)
def create(
    request: Dict[str, Any] | None = Body(
        ...,
        description="FHIR R4B Bundle resource containing referral information",
        example={
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "ServiceRequest",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/example"}
                    },
                    "request": {
                        "method": "POST",
                        "url": "ServiceRequest"
                    }
                }
            ]
        }
    ),
    bundle_registration_service: BundleRegistartionService = Depends(get_bundle_registration_service),
) -> Response:
    if request is None:
        logger.error("Resource is missing in the request")
        raise InvalidResourceException("Resource is missing in the request")

    bundle = Bundle.model_validate(request)
    results = bundle_registration_service.register(bundle)

    return JSONResponse(status_code=200, content=results.model_dump())
