import base64
import rfc8785
from typing import Any, Dict, Tuple

import pyoprf
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class OprfService:
    @staticmethod
    def create_blinded_input(
        personal_identifier: Dict[str, Any],
        recipient_organization: str,
        recipient_scope: str,
    ) -> Tuple[str, str]:
        info = f"{recipient_organization}|{recipient_scope}|v1".encode("utf-8")
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
        personal_id = rfc8785.dumps(personal_identifier)
        derived_personal_id = hkdf.derive(personal_id)
        blind_factor, blinded_input = pyoprf.blind(derived_personal_id)

        blind_factor_encoded = base64.urlsafe_b64encode(blind_factor).decode()
        blinded_input_encoded = base64.urlsafe_b64encode(blinded_input).decode()

        return blind_factor_encoded, blinded_input_encoded
