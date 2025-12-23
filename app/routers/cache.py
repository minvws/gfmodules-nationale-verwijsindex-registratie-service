from textwrap import dedent

from fastapi import APIRouter, Depends, Query

from app.container import get_synchronizer
from app.models.data_domain import DataDomain
from app.models.domains_map import DomainsMap
from app.services.synchronization.synchronizer import Synchronizer

router = APIRouter(prefix="/cache", tags=["Cache Management"])


@router.post(
    "/clear",
    summary="Clear Cache",
    description=dedent("""
    Clear the cache for a specific data domain or all domains.

    This endpoint allows you to clear cached data either for a specific domain or globally.

    **Use Cases:**
    - Clear specific domain cache after data updates
    - Force cache refresh for troubleshooting
    - Reset all caches during maintenance
    """),
    response_model=DomainsMap,
    responses={
        200: {
            "description": "Cache cleared successfully",
            "content": {
                "application/json": {
                    "example": {
                        "domain1": {"last_resource_update": "2025-11-25T10:30:00Z"},
                        "domain2": {"last_resource_update": "2025-11-25T09:15:00Z"},
                    }
                }
            },
        },
        500: {
            "description": "Invalid data domain specified",
            "content": {
                "application/json": {
                    "example": {
                        "resourceType": "OperationOutcome",
                        "issue": [
                            {
                                "severity": "error",
                                "code": "exception",
                                "details": {"text": "'domain1 is not known to defined list of DataDomains.'"},
                            }
                        ],
                    }
                }
            },
        },
    },
)
def clear_cache(
    data_domain: str | None = Query(
        None,
        description="The specific data domain to clear. If not provided, all domains will be cleared.",
        example="ImagingStudy",
    ),
    service: Synchronizer = Depends(get_synchronizer),
) -> DomainsMap:
    return service.clear_cache(DataDomain(data_domain))
