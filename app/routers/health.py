import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health() -> dict[str, Any]:
    # There are currently no systems to check for health status
    healthy = True

    return {"status": healthy}
