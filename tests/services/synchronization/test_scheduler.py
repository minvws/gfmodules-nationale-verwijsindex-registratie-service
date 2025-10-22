import time
from typing import Any, Callable, Generator

import pytest

from app.services.synchronization.scheduler import Scheduler


@pytest.fixture
def mock_function() -> Callable[..., None]:
    def hello_world() -> None:
        pass

    return hello_world


@pytest.fixture
def scheduler(mock_function: Callable[..., Any]) -> Generator[Scheduler, Any, Any]:
    sch = Scheduler(function=mock_function, delay=1)

    yield sch

    sch.stop()


def test_start_should_succeed_and_run_once(scheduler: Scheduler) -> None:
    scheduler.start()
    time.sleep(1.2)
    runners_history = scheduler.get_runners_history()
    assert len(runners_history) == 1


def test_stop_should_succeed_and_run_three_times(scheduler: Scheduler) -> None:
    scheduler.start()
    time.sleep(3.1)
    runner_history = scheduler.get_runners_history()

    assert len(runner_history) == 3
