import logging
from textwrap import dedent
from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from app import container
from app.services.metadata import MetadataService
from app.services.nvi import NviService
from app.services.pseudonym import PseudonymService

logger = logging.getLogger(__name__)
router = APIRouter()


def ok_or_error(value: bool) -> str:
    return "ok" if value else "error"


@router.get(
    "/health",
    summary="Health Check",
    description=dedent("""
    Comprehensive health check for all dependent API services and components.

    This endpoint performs health checks on all services required for the
    NVI Registration Service to function properly:

    **Checked Components:**
    - **pseudonym_service**: Pseudonymization/de-pseudonymization service
    - **referral_service**: National Referral Index (NVI) API
    - **metadata_api**: Metadata service for system information

    **Health Status:**
    - `ok`: Service is reachable and responding correctly
    - `error`: Service is unreachable or returning errors

    The overall status is `ok` only if all components are healthy.

    **Use Cases:**
    - Monitoring and alerting systems
    - container liveness/readiness probes
    - Manual service verification
    - Troubleshooting connectivity issues
    """),
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Health check completed (may contain unhealthy components)",
            "content": {
                "application/json": {
                    "examples": {
                        "all_healthy": {
                            "summary": "All services healthy",
                            "value": {
                                "status": "ok",
                                "components": {
                                    "pseudonym_service": "ok",
                                    "referral_service": "ok",
                                    "metadata_api": "ok",
                                },
                            },
                        },
                        "degraded": {
                            "summary": "Some services unhealthy",
                            "value": {
                                "status": "error",
                                "components": {
                                    "pseudonym_service": "ok",
                                    "referral_service": "error",
                                    "metadata_api": "ok",
                                },
                            },
                        },
                    }
                }
            },
        },
        500: {"description": "Unexpected error during health check execution"},
    },
    tags=["Health"],
)
def health(
    pseudonym_service: PseudonymService = Depends(container.get_pseudonym_service),
    referral_service: NviService = Depends(container.get_nvi_service),
    metadata_service: MetadataService = Depends(container.get_metadata_service),
) -> Dict[str, Any]:
    components = {
        "pseudonym_service": ok_or_error(pseudonym_service.server_healthy()),
        "referral_service": ok_or_error(referral_service.server_healthy()),
        "metadata_api": ok_or_error(metadata_service.server_healthy()),
    }
    healthy = ok_or_error(all(value == "ok" for value in components.values()))

    return {"status": healthy, "components": components}
