from unittest.mock import MagicMock, patch

from app.models.referrals import Referral
from app.services.registration.referrals import ReferralRegistrationService

PATCHED_OPRF = "app.services.registration.referrals.OprfService.create_blinded_input"
PATCHED_PSEUDONYM = "app.services.registration.referrals.PseudonymService.evaluate"
PATCHED_GET = "app.services.registration.referrals.NviService.get_registered_referrals"
PATCHED_ADD = "app.services.registration.referrals.NviService.add_referral"

BSN = "200060429"


@patch(PATCHED_ADD)
@patch(PATCHED_GET)
@patch(PATCHED_PSEUDONYM)
@patch(PATCHED_OPRF)
def test_register_should_succeed(
    mock_oprf: MagicMock,
    mock_evaluate: MagicMock,
    mock_get_registered: MagicMock,
    mock_add_referral: MagicMock,
    registration_service: ReferralRegistrationService,
    mock_referral: Referral,
) -> None:
    mock_oprf.return_value = ("blind_factor", "blinded_input")
    mock_evaluate.return_value = "evaluated_output"
    mock_get_registered.return_value = []
    mock_add_referral.return_value = mock_referral

    actual = registration_service.register(BSN)

    assert actual == mock_referral
    mock_add_referral.assert_called_once()


@patch(PATCHED_ADD)
@patch(PATCHED_GET)
@patch(PATCHED_PSEUDONYM)
@patch(PATCHED_OPRF)
def test_register_should_return_none_if_referral_exists(
    mock_oprf: MagicMock,
    mock_evaluate: MagicMock,
    mock_get_registered: MagicMock,
    mock_add_referral: MagicMock,
    registration_service: ReferralRegistrationService,
    mock_referral: Referral,
) -> None:
    mock_oprf.return_value = ("blind_factor", "blinded_input")
    mock_evaluate.return_value = "evaluated_output"
    mock_get_registered.return_value = [mock_referral]

    actual = registration_service.register(BSN)

    assert actual is None
    mock_add_referral.assert_not_called()
