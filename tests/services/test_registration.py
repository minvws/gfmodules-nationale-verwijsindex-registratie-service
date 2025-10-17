from unittest.mock import MagicMock, patch

from app.data import Pseudonym
from app.models.referrals import Referral
from app.services.registration import RegistrationService

PATCHED_NVI = "app.services.registration.NviService"
PATCHED_PSEUDONYM = "app.services.registration.PseudonymService.submit"


@patch(f"{PATCHED_NVI}.submit")
@patch(f"{PATCHED_NVI}.get_referrals")
@patch(PATCHED_PSEUDONYM)
def test_register_should_succeed(
    pseudonym_response: MagicMock,
    referral_query_response: MagicMock,
    new_referral_response: MagicMock,
    registration_service: RegistrationService,
    mock_referral: Referral,
    mock_pseudonym: Pseudonym,
    mock_bsn_number: str,
) -> None:
    pseudonym_response.return_value = mock_pseudonym
    referral_query_response.return_value = None
    new_referral_response.return_value = mock_referral

    actual = registration_service.register(mock_bsn_number, "ImagingStud")

    assert mock_referral == actual


@patch(f"{PATCHED_NVI}.get_referrals")
@patch(PATCHED_PSEUDONYM)
def test_regsiter_should_return_None_if_referral_exists(
    pseudonym_response: MagicMock,
    referral_query_response: MagicMock,
    registration_service: RegistrationService,
    mock_referral: Referral,
    mock_pseudonym: Pseudonym,
    mock_bsn_number: str,
) -> None:
    pseudonym_response.return_value = mock_pseudonym
    referral_query_response.return_value = mock_referral

    actual = registration_service.register(mock_bsn_number, "ImagingStudy")

    assert actual is None
