import hashlib

import requests

from app.models.pseudonym import Pseudonym, PseudonymCreateDto
from app.services.api.api_service import GfApiService


class PseudonymApiService(GfApiService[Pseudonym, PseudonymCreateDto]):
    def register(self, data: PseudonymCreateDto) -> Pseudonym:
        bytes_string = bytes(data.bsn, encoding="utf-8")
        bsn_hash = hashlib.sha256(bytes_string).hexdigest()

        payload = {"provider_id": data.provider_id, "bsn_hash": bsn_hash}
        response = requests.post(f"{self._base_url}/register", json=payload)
        response.raise_for_status()

        new_pseudonym = Pseudonym(**response.json())
        return new_pseudonym
