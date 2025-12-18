from textwrap import dedent
from typing import Dict, List
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.container import get_synchronizer
from app.models.data_domain import DataDomain
from app.models.update_scheme import UpdateScheme
from app.services.synchronization.synchronizer import Synchronizer

router = APIRouter(prefix="/synchronize", tags=["Synchronizer"])


@router.post(
    "",
    response_model=Dict[str, List[UpdateScheme]],
    summary="Synchronize Data Domain",
    description=dedent("""
    Synchronize local referrals with the National Referral Index (NVI) for one or all domains.

    This endpoint triggers a single synchronization of referral data into the NVI service.
    It can operate on a specific data domain or synchronize all configured domains.

    Automatically pulls data from FHIR-store and creates referrals in the NVI service accordingly.

    **Data Domains:**
    Data domains represent different categories or sources of referral data.
    Each domain maintains its own synchronization state and timestamp.
    Data domains must be enabled and pre-configured in the system.

    **Use Cases:**
    - Keep NVI referrals up-to-date with latest local data
    - On-demand refresh for specific domains
    """),
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Synchronization completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "patient-data": [
                            {
                                "updated_data": [
                                    {
                                        "bsn": "123456789",
                                        "referral": {
                                            "pseudonym": "pseudo123",
                                            "data_domain": "ImagingStudy",
                                            "ura_number": "12345678",
                                        },
                                    }
                                ],
                                "domain_entry": {"last_resource_update": "2025-11-25T10:30:00Z"},
                            }
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Invalid data domain specified",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid data_domain. Must be one of: ImagingStudy, MedicationStatement"}
                }
            },
        },
        500: {
            "description": "Internal server error during synchronization",
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
def synchronize_domain(
    data_domain: str | None = Query(
        None,
        description="""The specific data domain to synchronize. If not provided, all configured domains will be synchronized.
        Domain names are case-sensitive and must match configured values.""",
        example="ImagingStudy",
    ),
    service: Synchronizer = Depends(get_synchronizer),
) -> Dict[str, List[UpdateScheme]]:
    if data_domain is not None:
        allowed_domains = service.get_allowed_domains()
        if data_domain not in allowed_domains:
            raise HTTPException(
                status_code=400, detail=f"Invalid data_domain. Must be one of: {', '.join(str(data_domain) for data_domain in allowed_domains)}"
            )
        return service.synchronize_domain(DataDomain(quote(data_domain)))
    else:
        return service.synchronize_all_domains()
