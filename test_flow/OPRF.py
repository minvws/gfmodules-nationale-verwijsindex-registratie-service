import base64
import json
from typing import Dict, Tuple

import pyoprf
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from test_flow.data import NVI_URA_NUMBER


class OPRF:
    @staticmethod
    def create_blinded_input(
        personal_identifier: Dict[str, str],
        recipient_organization: str,
        recipient_scope: str,
    ) -> Tuple[str, str]:
        """
        C
        reates a blinded input from an PersonalIdentifier, recipient_organization and recipient_scope for OPRF operations.

        Returns:
            Tuple of (blind_factor, blinded_input) both base64 encoded
        """
        info = f"{recipient_organization}|{recipient_scope}|v1".encode("utf-8")
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
        pid = json.dumps(personal_identifier)
        pseudonym = hkdf.derive(pid.encode("utf-8"))

        blind_factor, blinded_input = pyoprf.blind(pseudonym)

        blind_factor_encoded = base64.urlsafe_b64encode(blind_factor).decode()
        blinded_input_encoded = base64.urlsafe_b64encode(blinded_input).decode()

        return blind_factor_encoded, blinded_input_encoded


if __name__ == "__main__":
    personal_identifier = {
        "landCode": "NL",
        "type": "BSN",
        "value": "123456789",
    }
    recepient_org = f"ura:{NVI_URA_NUMBER}"
    recipient_scope = "nationale-verwijsindex"

    blinded_factor, blinded_input = OPRF.create_blinded_input(
        personal_identifier=personal_identifier,
        recipient_organization=recepient_org,
        recipient_scope=recipient_scope,
    )
    print("oprf_key", blinded_factor)
    print("blinded input", blinded_input)
