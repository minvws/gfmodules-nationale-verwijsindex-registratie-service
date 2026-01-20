import logging
from collections.abc import Callable
from datetime import datetime
from threading import Event, Thread
from typing import Any

logger = logging.Logger(__name__)


class Scheduler:
    def __init__(self, function: Callable[..., Any], delay: int) -> None:
        self.__function = function
        self.__delay = delay
        self.__thread: Thread | None = None
        self.__stop_event: Event = Event()
        self.__runner_id = 1
        self.__runners_history: list[dict[int, Any]] = []

    def start(self) -> None:
        print("Starting scheduler")
        if self.__thread is not None:
            print("already running")
            return

        if self.__stop_event.is_set() is True:
            self.__stop_event.clear()

        print("Starting thread")
        self.__thread = Thread(target=self.__run)
        self.__thread.start()
        logger.info(f"starting thread: {self.__thread.getName()}")

    def stop(self) -> None:
        print("stopping thread")
        if self.__thread is not None:
            print("stopping thread real")
            self.__stop_event.set()
            self.__thread.join()
            self.__thread = None

    def get_runners_history(self) -> list[dict[int, Any]]:
        return self.__runners_history

    def __run(self) -> None:
        while self.__stop_event.is_set() is False:
            try:
                self.__function()
            except Exception as e:
                logger.error(f"Error in scheduled function: {e}")
            self.__stop_event.wait(self.__delay)
            self.__update_runner()

    def __update_runner(self) -> None:
        data = {"executed_at": datetime.now().isoformat()}
        if self.__thread is not None:
            data.update({"thread": self.__thread.getName()})
        self.__runners_history.append({self.__runner_id: data})
        self.__runner_id += 1
