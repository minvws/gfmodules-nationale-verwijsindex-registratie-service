from fastapi import APIRouter, Depends

from app.container import get_synchronizer
from app.data import DataDomain
from app.models.domains_map import DomainsMap
from app.services.synchronizer import Synchronizer

router = APIRouter(prefix="/cache", tags=["Cache Management"])


@router.post("/clear")
def clear_cache(data_domain: DataDomain | None = None, service: Synchronizer = Depends(get_synchronizer)) -> DomainsMap:
    return service.clear_cache(data_domain)
