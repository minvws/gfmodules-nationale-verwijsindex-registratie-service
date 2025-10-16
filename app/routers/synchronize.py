from typing import Dict, List

from fastapi import APIRouter, Depends

from app.container import get_synchronizer
from app.models.update_scheme import UpdateScheme
from app.services.synchronizer import Synchronizer

router = APIRouter(prefix="/synchronize", tags=["Synchronizer"])


@router.post(
    "",
    response_model=None,
    description="Synchronize a specific data domain or all domains",
)
def synchronize_domain(
    data_domain: str | None = None, service: Synchronizer = Depends(get_synchronizer)
) -> Dict[str, List[UpdateScheme]]:
    # dd = DataDomain.from_str(data_domain) if data_domain else None
    if data_domain is not None:
        return service.synchronize_domain(data_domain)
    else:
        return service.synchronize_all_domains()
