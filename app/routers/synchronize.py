from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from urllib.parse import quote

from app.container import get_synchronizer
from app.models.update_scheme import UpdateScheme
from app.services.synchronization.synchronizer import Synchronizer

router = APIRouter(prefix="/synchronize", tags=["Synchronizer"])


@router.post(
    "",
    response_model=Dict[str, List[UpdateScheme]],
    summary="Synchronize Data Domain",
    description="""Synchronize referral data from the National Referral Index (NVI) for one or all domains.
    
    This endpoint triggers synchronization of referral data from the NVI service into the local cache.
    It can operate on a specific data domain or synchronize all configured domains.
    
    **Synchronization Process:**
    1. Queries the NVI service for updated referrals since last sync
    2. Retrieves BSN (patient identifier) mappings
    3. Processes and stores referral data locally
    4. Updates domain metadata with last sync timestamp
    5. Returns summary of synchronized data per domain
    
    **Data Domains:**
    Data domains represent different categories or sources of referral data.
    Each domain maintains its own synchronization state and timestamp.
    
    **Use Cases:**
    - Periodic synchronization to keep data up-to-date
    - On-demand refresh for specific domains
    - Initial data load for new domains
    - Recovery after service disruptions
    """,
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
                                            "data_domain": "patient-data",
                                            "ura_number": "12345678"
                                        }
                                    }
                                ],
                                "domain_entry": {
                                    "last_resource_update": "2025-11-25T10:30:00Z"
                                }
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Invalid data domain specified",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid data_domain. Must be one of: domain1, domain2, domain3"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during synchronization"
        },
        503: {
            "description": "NVI service unavailable"
        }
    }
)
def synchronize_domain(
    data_domain: str | None = Query(
        None,
        description="""The specific data domain to synchronize. If not provided, all configured domains will be synchronized.
        Domain names are case-sensitive and must match configured domain identifiers.""",
        example="patient-data"
    ),
    service: Synchronizer = Depends(get_synchronizer)
) -> Dict[str, List[UpdateScheme]]:
    if data_domain is not None:
        allowed_domains = service.get_allowed_domains()
        if data_domain not in allowed_domains:
            raise HTTPException(
                status_code=400, detail=f"Invalid data_domain. Must be one of: {', '.join(allowed_domains)}"
            )
        return service.synchronize_domain(quote(data_domain))
    else:
        return service.synchronize_all_domains()
