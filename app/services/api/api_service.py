import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import requests
from pydantic import BaseModel
from requests.exceptions import ConnectionError, Timeout

T = TypeVar("T", bound=BaseModel)
TArgs = TypeVar("TArgs", bound=BaseModel)

logger = logging.getLogger(__name__)


class ApiService(ABC):
    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def _base_url(self) -> str:
        return self._url

    @_base_url.setter
    def _base_url(self, url: str) -> None:
        self._url = url

    @abstractmethod
    def api_healthy(self) -> bool: ...

    def _api_healthy(self, sub_route: str) -> bool:
        try:
            response = requests.get(f"{self._base_url}/{sub_route}")
            if response.status_code >= 400:
                return False
        except (ConnectionError, Timeout) as e:
            logger.error(e)
            return False

        return True


class GfApiService(ApiService, ABC, Generic[T, TArgs]):
    def api_healthy(self) -> bool:
        return self._api_healthy("health")

    @abstractmethod
    def register(self, data: TArgs) -> T: ...


class FhirApiService(ApiService, ABC):
    def api_healthy(self) -> bool:
        return self._api_healthy("metadata")
