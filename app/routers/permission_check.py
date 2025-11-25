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
    description="""Check if a patient has given permission to share referral data with an organization.
    
    This endpoint verifies authorization for data access by checking if the patient
    has provided consent for the requesting organization (identified by URA number)
    to access their referral information.
    
    **Authorization Flow:**
    1. Receives encrypted patient identifier (LMR ID)
    2. Receives requesting organization's URA number
    3. Queries the OTV (Permission Service) for consent status
    4. Returns boolean indicating whether access is permitted
    
    **Security:**
    - Uses encrypted identifiers to protect patient privacy
    - Validates URA numbers for organizational authentication
    - Enforces patient consent policies
    """,
    response_model=bool,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Permission check completed successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "granted": {
                            "summary": "Permission granted",
                            "value": True
                        },
                        "denied": {
                            "summary": "Permission denied",
                            "value": False
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid request parameters (e.g., malformed URA number)",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid URA number format"}
                }
            }
        },
        422: {
            "description": "Validation error in request payload"
        },
        500: {
            "description": "Internal server error during permission check"
        },
        503: {
            "description": "OTV Permission Service unavailable"
        }
    }
)
def check_permission(
    payload: PermissionRequestModel = Body(
        ...,
        description="Permission check request containing encrypted patient ID and organization URA number",
        example={
            "encrypted_lmr_id": "abc123def456encrypted",
            "client_ura_number": "12345678"
        }
    ),
    auth_service: AuthorizationCheckService = Depends(get_authorization_check_service),
) -> bool:
    return auth_service.authorize(payload)
