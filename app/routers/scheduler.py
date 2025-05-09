from typing import Any

from fastapi import APIRouter, Depends

from app.container import get_scheduler
from app.services.scheduler import Scheduler

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.post("/start")
def start_scheduler(service: Scheduler = Depends(get_scheduler)) -> None:
    return service.start()


@router.post("/stop")
def stop_scheduler(service: Scheduler = Depends(get_scheduler)) -> None:
    return service.stop()


@router.get("/runners-history")
def get_runners_history(
    service: Scheduler = Depends(get_scheduler),
) -> list[dict[int, Any]]:
    return service.get_runners_history()
