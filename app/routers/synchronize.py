from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.container import get_synchronizer
from app.models.update_scheme import UpdateScheme
from app.services.synchronization.synchronizer import Synchronizer

router = APIRouter(prefix="/synchronize", tags=["Synchronizer"])


@router.post(
    "",
    response_model=None,
    description="Synchronize a specific data domain or all domains",
)
def synchronize_domain(
    data_domain: str | None = None, service: Synchronizer = Depends(get_synchronizer)
) -> Dict[str, List[UpdateScheme]]:
    if data_domain is not None:
        allowed_domains = service.get_allowed_domains()
        if data_domain not in allowed_domains:
            raise HTTPException(
                status_code=400, detail=f"Invalid data_domain. Must be one of: {', '.join(allowed_domains)}"
            )
        return service.synchronize_domain(data_domain)
    else:
        return service.synchronize_all_domains()
