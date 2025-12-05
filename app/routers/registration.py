import logging
from textwrap import dedent
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, status
from fhir.resources.R4B.bundle import Bundle
from starlette.responses import JSONResponse, Response

from app.container import (
    get_bundle_registration_service,
)
from app.exceptions.service_exceptions import InvalidResourceException
from app.services.registration.bundle import BundleRegistrationService

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/registration",
    tags=["Registration Service"],
)


@router.post(
    "",
    summary="Create Referral Registration",
    description=dedent("""
    Register a referral through a FHIR R4B bundle.

    This endpoint processes FHIR R4B Bundle resources containing referral information.
    The bundle should include all necessary resources for registering a patient referral
    in the National Referral Index (NVI).

    **Request Requirements:**
    - Must be a valid FHIR R4B Bundle resource
    - Should contain referral-related resources (ImagingStudy, CarePlan, etc.)
    - Should contain the referenced Patient resource(s)

    **Use Cases:**
    - Manually register new patient referrals in the NVI system
    - Specific situations where automated referral registration is not suitable
    """),
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Referral registered successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "successful_registration": {
                            "summary": "Successful registration response",
                            "value": {
                                "resourceType": "Bundle",
                                "type": "transaction-response",
                                "entry": [
                                    {"response": {"status": "201 Created", "location": "ServiceRequest/example-id"}}
                                ],
                            },
                        }
                    }
                }
            },
        },
        400: {
            "description": "Invalid FHIR bundle or missing required resources",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "resourceType": "OperationOutcome",
                            "issue": [
                                {
                                    "severity": "error",
                                    "code": "exception",
                                    "details": {"text": "Invalid bundle without entries"},
                                }
                            ],
                        }
                    }
                }
            },
        },
        500: {
            "description": "Internal server error during registration",
            "content": {
                "application/json": {
                    "example": {
                        "resourceType": "OperationOutcome",
                        "issue": [
                            {
                                "severity": "error",
                                "code": "exception",
                                "details": {"text": "Failed to exchange BSN for pseudonym"},
                            }
                        ],
                    }
                }
            },
        },
    },
)
def create(
    request: Dict[str, Any] | None = Body(
        description="FHIR R4B Bundle resource containing referral information",
        example={
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "example-patient-1",
                        "name": [{"text": "Mohammed Koster"}],
                        "identifier": [{"system": "http://fhir.nl/fhir/NamingSystem/bsn", "value": "468467543"}],
                    }
                },
                {
                    "resource": {
                        "resourceType": "CarePlan",
                        "id": "example-careplan-1",
                        "status": "completed",
                        "intent": "plan",
                        "title": "Random CarePlan",
                        "description": "random description",
                        "subject": {"reference": "Patient/example-patient-1", "display": "Mohammed Koster"},
                        "careTeam": [
                            {"reference": "CareTeam/example-careteam-1", "display": "Care Team 1"},
                            {"reference": "CareTeam/example-careteam-2", "display": "Care Team 2"},
                        ],
                    }
                },
            ],
        },
    ),
    bundle_registration_service: BundleRegistrationService = Depends(get_bundle_registration_service),
) -> Response:
    if request is None:
        logger.error("Resource is missing in the request")
        raise InvalidResourceException("Resource is missing in the request")

    bundle = Bundle.model_validate(request)
    results = bundle_registration_service.register(bundle)

    return JSONResponse(status_code=200, content=results.model_dump())
