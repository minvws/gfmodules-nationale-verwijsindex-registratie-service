import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


def ok_or_error(value: bool) -> str:
    return "ok" if value else "error"


@router.get("/health")
def health() -> dict[str, Any]:
    components = {}
    healthy = ok_or_error(all(value == "ok" for value in components.values()))

    return {"status": healthy, "components": components}
