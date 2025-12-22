import logging
from dataclasses import dataclass
from typing import Any, Self

from uzireader.uzi import UziException
from uzireader.uziserver import UziServer

logger = logging.getLogger(__name__)


@dataclass
class UraNumber:
    """
    Representation of an URA Number, where it can adhere to the requirements
    of that number.
    See: https://www.zorgcsp.nl/documents/10-01-2025%20RK1%20CPS%20UZI-register%20V11.9%20NL.pdf
    """

    value: str

    def __init__(self, value: Any) -> None:
        if (isinstance(value, int) or isinstance(value, str)) and len(str(value)) <= 8 and str(value).isdigit():
            self.value = str(value).zfill(8)
        else:
            raise ValueError("URA number must be 8 digits or less")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"UraNumber({self.value})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, UraNumber):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    @classmethod
    def from_certificate(cls, cert_data: str) -> Self | None:
        try:
            uzi_server = UziServer(verify="SUCCESS", cert=cert_data)
            subscriber_number = uzi_server["SubscriberNumber"]

            return cls(subscriber_number)

        except UziException as e:
            logger.error(e)
            return None
