import logging

from app.models.referrals import ReferralQuery, ReferralEntity, CreateReferralRequest
from app.services.api.http_service import GfHttpService
from app.services.api.oauth import OauthService
from app.services.fhir.nvi_data_reference import NviDataReferenceMapper

logger = logging.getLogger(__name__)


class NviService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        fhir_mapper: NviDataReferenceMapper,
        oauth_service: OauthService,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ca: str | bool = True,
    ):
        self.http_service = GfHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            verify_ca=verify_ca,
        )
        self.oauth_service = oauth_service
        self.fhir_mapper = fhir_mapper

    def is_referral_registered(self, payload: ReferralQuery) -> bool:
        try:
            token = self.oauth_service.fetch_token(scope=["epd:read"])
            response = self.http_service.do_request(
                method="GET",
                sub_route="NVIDataReference",
                params=payload.model_dump(mode="json", by_alias=True),
                headers={
                    "Authorization": f"Bearer {token.access_token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch referrals: {e}")
            raise e
        decoded = response.json()
        entries = decoded.get("entry", [])
        if len(entries) == 0:
            return False
        return True

    def submit(self, data: CreateReferralRequest) -> ReferralEntity:
        token = self.oauth_service.fetch_token(scope=["epd:write"])
        response = self.http_service.do_request(
            method="POST",
            sub_route="NVIDataReference",
            json=self.fhir_mapper.to_fhir(data),
            headers={
                "Authorization": f"Bearer {token.access_token}",
                "Content-Type": "application/fhir+json",
            },
        )
        response.raise_for_status()
        resp = response.json()
        logging.info(f"Updating NVI with new referrals: {resp}")
        new_referral = ReferralEntity.from_nvi_fhir(resp)
        return new_referral

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
