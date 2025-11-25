from typing import Any

from fastapi import APIRouter, Depends

from app.container import get_scheduler
from app.services.synchronization.scheduler import Scheduler

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.post("/start", summary="Start the scheduler", description="If not already running, starts a background scheduler thread")
def start_scheduler(service: Scheduler = Depends(get_scheduler)) -> None:
    return service.start()


@router.post("/stop", summary="Stop the scheduler", description="Stops the background scheduler thread if it is running")
def stop_scheduler(service: Scheduler = Depends(get_scheduler)) -> None:
    return service.stop()


@router.get("/runners-history", summary="Get Runners History", description="Get the history of all runners")
def get_runners_history(
    service: Scheduler = Depends(get_scheduler),
) -> list[dict[int, Any]]:
    return service.get_runners_history()
