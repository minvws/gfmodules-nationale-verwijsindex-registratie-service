import enum
import uuid
from dataclasses import dataclass
from typing import Any

BSN_SYSTEM = "http://fhir.nl/fhir/NamingSystem/bsn"  # NOSONAR


@dataclass
class Pseudonym:
    def __init__(self, value: Any) -> None:
        self.value = uuid.UUID(str(value))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Pseudonym({self.value})"


class OutcomeResponseStatusCode(int, enum.Enum):
    CREATED = 201
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


class OutcomeResponseSeverity(str, enum.Enum):
    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"


class OutcomeResponseCode(str, enum.Enum):
    CREATED = "created"
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    EXCEPTION = "exception"
