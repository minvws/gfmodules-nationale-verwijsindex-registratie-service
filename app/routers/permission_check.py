from textwrap import dedent

from fastapi import APIRouter, Body, Depends, status

from app.container import get_authorization_check_service
from app.models.permission import PermissionRequestModel
from app.services.authorization_check_service import AuthorizationCheckService

router = APIRouter(
    prefix="/authorize",
    tags=["Permission Check Service"],
)


@router.post(
    "",
    summary="Permission Check",
    description=dedent("""
    Check if a patient has given permission to share registered data with an organization.
    
    This endpoint verifies authorization for data access in the OTV by checking if the patient
    has provided consent for the requesting organization (identified by URA number)
    to access their data through the registered referral.
    
    - Uses encrypted identifiers to protect patient privacy
    - Validates URA numbers for organizational authentication
    - Enforces patient consent policies
    """),
    response_model=bool,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Permission check completed successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "granted": {"summary": "Permission granted", "value": True},
                        "denied": {"summary": "Permission denied", "value": False},
                    }
                }
            },
        },
        422: {
            "description": "Invalid request parameters (e.g., malformed URA number)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "value_error",
                                "loc": ["body"],
                                "msg": "Value error, UraNumber must be 8 digits or less",
                                "input": {
                                    "encrypted_lmr_id": "abc123def456encrypted",
                                    "client_ura_number": "123456789",
                                },
                                "ctx": {"error": {}},
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal server error during permission check",
            "content": {
                "application/json": {
                    "example": {
                        "resourceType": "OperationOutcome",
                        "issue": [
                            {
                                "severity": "error",
                                "code": "exception",
                                "details": {"text": "Failed to check for authorization"},
                            }
                        ],
                    }
                }
            },
        },
    },
)
def check_permission(
    payload: PermissionRequestModel = Body(
        description="Permission check request containing encrypted patient ID and organization URA number",
        example={"encrypted_lmr_id": "abc123def456encrypted", "client_ura_number": "12345678"},
    ),
    auth_service: AuthorizationCheckService = Depends(get_authorization_check_service),
) -> bool:
    return auth_service.authorize(payload)
