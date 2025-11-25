from textwrap import dedent
from typing import Any

from fastapi import APIRouter, Depends, status

from app.container import get_scheduler
from app.services.synchronization.scheduler import Scheduler

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.post(
    "/start",
    summary="Start the Scheduler",
    description=dedent("""
    Start the background scheduler thread for automatic synchronization.
    
    The scheduler runs periodic tasks to synchronize referral data from the NVI service.
    If the scheduler is already running, this endpoint has no effect.
    
    **Scheduler Behavior:**
    - Runs as a background thread
    - Executes synchronization tasks at configured intervals
    - Automatically handles errors and retries
    - Maintains execution history for monitoring
    
    **Use Cases:**
    - Enable automatic periodic synchronization
    - Resume scheduled tasks after manual stop
    - Initialize scheduler after service startup
    """),
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Scheduler started successfully or was already running", "content": None},
        500: {"description": "Failed to start scheduler"},
    },
)
def start_scheduler(service: Scheduler = Depends(get_scheduler)) -> None:
    return service.start()


@router.post(
    "/stop",
    summary="Stop the Scheduler",
    description=dedent("""
    Stop the background scheduler thread.
    
    This endpoint gracefully stops the scheduler, allowing any currently running
    synchronization tasks to complete before shutting down. If the scheduler is
    not running, this endpoint has no effect.
    
    **Use Cases:**
    - Temporarily disable automatic synchronization
    - Perform maintenance without scheduled interruptions
    - Control resource usage during high-load periods
    """),
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Scheduler stopped successfully or was not running", "content": None},
        500: {"description": "Failed to stop scheduler"},
    },
)
def stop_scheduler(service: Scheduler = Depends(get_scheduler)) -> None:
    return service.stop()


@router.get(
    "/runners-history",
    summary="Get Runners History",
    description=dedent("""
    Retrieve the execution history of all scheduled synchronization runners.
    """),
    response_model=list[dict[int, Any]],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Runners history retrieved successfully", "content": None},
        500: {"description": "Failed to retrieve runners history"},
    },
)
def get_runners_history(
    service: Scheduler = Depends(get_scheduler),
) -> list[dict[int, Any]]:
    return service.get_runners_history()
