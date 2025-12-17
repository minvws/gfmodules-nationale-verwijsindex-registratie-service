import base64

from app.models.pseudonym import PersonalIdentifier
from app.services.oprf import OprfService


def test_create_blinded_input() -> None:
    personal_identifier = PersonalIdentifier(
        land_code="NL",
        type="bsn",
        value="123456789",
    )
    recipient_organization = "test_org"
    recipient_scope = "test_scope"

    blind_factor_encoded, blinded_input_encoded = OprfService.create_blinded_input(
        personal_identifier, recipient_organization, recipient_scope
    )

    assert isinstance(blind_factor_encoded, str)
    assert isinstance(blinded_input_encoded, str)

    assert base64.urlsafe_b64decode(blind_factor_encoded)
    assert base64.urlsafe_b64decode(blinded_input_encoded)
