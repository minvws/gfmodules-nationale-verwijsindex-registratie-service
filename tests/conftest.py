from datetime import datetime

import pytest

from app.models.pseudonym import Pseudonym
from app.models.referrals import CreateReferralDTO, Referral, ReferralQueryDTO
from app.models.update_scheme import BsnUpdateScheme
from app.services.domain_map_service import DomainsMapService
from app.services.metadata import MetadataService
from app.services.nvi import NviService
from app.services.pseudonym import PseudonymService
from app.services.synchronizer import Synchronizer


@pytest.fixture
def mock_url() -> str:
    return "http://example.org"


@pytest.fixture
def mock_ura_number() -> str:
    return "12345678"


@pytest.fixture
def domains_map_service() -> DomainsMapService:
    return DomainsMapService()


@pytest.fixture
def pseudonym_service(mock_url: str, mock_ura_number: str) -> PseudonymService:
    return PseudonymService(
        provider_id=mock_ura_number,
        endpoint=mock_url,
        timeout=1,
        mtls_cert=None,
        mtls_key=None,
        mtls_ca=None,
    )


@pytest.fixture
def nvi_service(mock_url: str) -> NviService:
    return NviService(
        endpoint=mock_url, timeout=1, mtls_cert=None, mtls_key=None, mtls_ca=None
    )


@pytest.fixture
def metadata_service(mock_url: str) -> MetadataService:
    return MetadataService(
        endpoint=mock_url, timeout=1, mtls_cert=None, mtls_key=None, mtls_ca=None
    )


@pytest.fixture
def synchronizer(
    domains_map_service: DomainsMapService,
    pseudonym_service: PseudonymService,
    nvi_service: NviService,
    metadata_service: MetadataService,
    mock_ura_number: str,
) -> Synchronizer:
    return Synchronizer(
        nvi_api=nvi_service,
        pseudonym_api=pseudonym_service,
        metadata_api=metadata_service,
        domains_map_service=domains_map_service,
        ura_number=mock_ura_number,
    )


@pytest.fixture
def referral_query() -> ReferralQueryDTO:
    return ReferralQueryDTO(
        pseudonym="some_pseudonym", data_domain="some_domain", ura_number="1234566789"
    )


@pytest.fixture
def create_referral_dto(referral_query: ReferralQueryDTO) -> CreateReferralDTO:
    return CreateReferralDTO(
        **referral_query.model_dump(), requesting_uzi_number="some_uzi_number"
    )


@pytest.fixture
def mock_bsn_number() -> str:
    return "200060429"


@pytest.fixture
def datetime_past() -> str:
    return datetime(2022, 12, 10, 12, 0, 0, 0).isoformat()


@pytest.fixture
def datetime_now() -> str:
    return datetime(2025, 12, 10, 12, 0, 0, 0).isoformat()


@pytest.fixture
def mock_pseudonym() -> Pseudonym:
    return Pseudonym(pseudonym="some_pseudonym")


@pytest.fixture
def mock_referral(mock_ura_number: str, mock_pseudonym: Pseudonym) -> Referral:
    return Referral(
        pseudonym=mock_pseudonym.pseudonym,
        data_domain="beeldbank",
        ura_number=mock_ura_number,
    )


@pytest.fixture
def bsn_update_scheme(mock_bsn_number: str, mock_referral: Referral) -> BsnUpdateScheme:
    return BsnUpdateScheme(bsn=mock_bsn_number, referral=mock_referral)
