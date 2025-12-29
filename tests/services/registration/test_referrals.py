from unittest.mock import MagicMock, patch

from app.models.bsn import BSN
from app.models.data_domain import DataDomain
from app.models.pseudonym import OprfPseudonymJWE
from app.models.referrals import ReferralEntity
from app.services.registration.referrals import ReferralRegistrationService

PATCHED_NVI = "app.services.registration.referrals.NviService"
PATCHED_PSEUDONYM = "app.services.registration.referrals.PseudonymService.submit"


@patch(f"{PATCHED_NVI}.submit")
@patch(f"{PATCHED_NVI}.is_referral_registered")
@patch(PATCHED_PSEUDONYM)
def test_register_should_succeed(
    pseudonym_response: MagicMock,
    referral_query_response: MagicMock,
    new_referral_response: MagicMock,
    registration_service: ReferralRegistrationService,
    mock_referral: ReferralEntity,
    mock_pseudonym_jwe: OprfPseudonymJWE,
    mock_bsn: BSN,
) -> None:
    pseudonym_response.return_value = mock_pseudonym_jwe
    referral_query_response.return_value = None
    new_referral_response.return_value = mock_referral

    actual = registration_service.register(mock_bsn, DataDomain("ImagingStudy"))

    assert mock_referral == actual


@patch(f"{PATCHED_NVI}.is_referral_registered")
@patch(PATCHED_PSEUDONYM)
def test_register_should_return_none_if_referral_exists(
    pseudonym_response: MagicMock,
    referral_query_response: MagicMock,
    registration_service: ReferralRegistrationService,
    mock_referral: ReferralEntity,
    mock_pseudonym_jwe: OprfPseudonymJWE,
    mock_bsn: BSN,
) -> None:
    pseudonym_response.return_value = mock_pseudonym_jwe
    referral_query_response.return_value = mock_referral

    actual = registration_service.register(mock_bsn, DataDomain("ImagingStudy"))

    assert actual is None
