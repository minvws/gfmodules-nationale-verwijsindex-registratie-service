from typing import Any

from fastapi import APIRouter, Depends, status

from app.container import get_scheduler
from app.services.synchronization.scheduler import Scheduler

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.post(
    "/start",
    summary="Start the Scheduler",
    description="""Start the background scheduler thread for automatic synchronization.
    
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
    """,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Scheduler started successfully or was already running"
        },
        500: {
            "description": "Failed to start scheduler"
        }
    }
)
def start_scheduler(service: Scheduler = Depends(get_scheduler)) -> None:
    return service.start()


@router.post(
    "/stop",
    summary="Stop the Scheduler",
    description="""Stop the background scheduler thread.
    
    This endpoint gracefully stops the scheduler, allowing any currently running
    synchronization tasks to complete before shutting down. If the scheduler is
    not running, this endpoint has no effect.
    
    **Important Notes:**
    - Current tasks will complete before shutdown
    - No new synchronization tasks will be started
    - Manual synchronization via /synchronize endpoint remains available
    - Scheduler state persists until service restart or manual start
    
    **Use Cases:**
    - Temporarily disable automatic synchronization
    - Perform maintenance without scheduled interruptions
    - Control resource usage during high-load periods
    """,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Scheduler stopped successfully or was not running"
        },
        500: {
            "description": "Failed to stop scheduler"
        }
    }
)
def stop_scheduler(service: Scheduler = Depends(get_scheduler)) -> None:
    return service.stop()


@router.get(
    "/runners-history",
    summary="Get Runners History",
    description="""Retrieve the execution history of all scheduled synchronization runners.
    
    This endpoint provides detailed information about past synchronization runs,
    including timestamps, execution status, and any errors encountered.
    
    **History Information:**
    - Execution timestamps
    - Success/failure status
    - Domains synchronized
    - Error messages (if any)
    - Execution duration
    
    **Use Cases:**
    - Monitor synchronization performance
    - Troubleshoot synchronization failures
    - Audit synchronization activities
    - Track data freshness
    """,
    response_model=list[dict[int, Any]],
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Runners history retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            1: {
                                "timestamp": "2025-11-25T10:00:00Z",
                                "status": "success",
                                "domains": ["patient-data", "referral-data"],
                                "duration_seconds": 45
                            }
                        },
                        {
                            2: {
                                "timestamp": "2025-11-25T09:00:00Z",
                                "status": "failed",
                                "domains": ["patient-data"],
                                "error": "NVI service timeout",
                                "duration_seconds": 120
                            }
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Failed to retrieve runners history"
        }
    }
)
def get_runners_history(
    service: Scheduler = Depends(get_scheduler),
) -> list[dict[int, Any]]:
    return service.get_runners_history()
