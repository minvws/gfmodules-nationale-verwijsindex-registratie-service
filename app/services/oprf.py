import base64
from typing import Tuple

import pyoprf
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.models.pseudonym import PersonalIdentifier


class OprfService:
    @staticmethod
    def create_blinded_input(
        personal_identifier: PersonalIdentifier, recipient_organization: str, recipient_scope: str
    ) -> Tuple[str, str]:
        """
        Creates a blinded input from an PersonalIdentifier, recipient_organization and recipient_scope for OPRF operations.

        Returns:
            Tuple of (blind_factor, blinded_input) both base64 encoded
        """
        # Create hashed bsn that is dedicated for the given receiver
        info = f"{recipient_organization}|{recipient_scope}|v1".encode("utf-8")
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
        pid = personal_identifier.model_dump_json(by_alias=True)
        pseudonym = hkdf.derive(pid.encode("utf-8"))

        # Create blinded input. This will mask the BSN so we can send it directly to the PRS
        blind_factor, blinded_input = pyoprf.blind(pseudonym)

        blind_factor_encoded = base64.urlsafe_b64encode(blind_factor).decode()
        blinded_input_encoded = base64.urlsafe_b64encode(blinded_input).decode()

        return blind_factor_encoded, blinded_input_encoded
