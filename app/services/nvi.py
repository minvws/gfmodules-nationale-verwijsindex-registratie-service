import logging
from typing import Any, Dict, List


from app.models.referrals import Referral
from app.models.token import AccessToken
from app.services.api.http_service import GfHttpService
from app.services.fhir.fhir_mapper import FhirMapper
from app.services.oauth.oauth_service import OauthService

logger = logging.getLogger(__name__)


class NviService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        fhir_mapper: FhirMapper,
        oauth_service: OauthService,
        org_registration_ura: str,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ca: str | bool = True,
        source_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ):
        self.endpoint = endpoint
        self.http_service = GfHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            verify_ca=verify_ca,
            extra_headers=extra_headers,
        )
        self.oauth_service = oauth_service
        self.fhir_mapper = fhir_mapper
        self.org_registration_ura = org_registration_ura
        self.source_id = source_id

    def _access_nvi_api(
        self,
        token: AccessToken,
        params: Dict[str, Any] | None = None,
        data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if params and data:
            raise ValueError("Cannot provide both params and data for the request.")
        try:
            response = self.http_service.do_request(
                method="GET" if data is None else "POST",
                sub_route="fhir/List",
                params=params,
                json=data,
                headers={
                    "Authorization": f"Bearer {token.access_token}",
                    "Content-Type": ("application/x-www-form-urlencoded" if data is None else "application/fhir+json"),
                },
            )
            response.raise_for_status()
            return response.json()  # type: ignore
        except Exception:
            logger.exception("Failed to access NVI API with params: %s and data: %s", params, data)
            raise

    def _query_referrals(self, token: AccessToken, subject: str, source_id: str | None = None) -> List[Referral]:
        try:
            params: Dict[str, Any] = {"subject:identifier": f"{self.fhir_mapper.subject_system}|{subject}"}
            if source_id:
                params["source:identifier"] = f"{self.fhir_mapper.source_system}|{source_id}"
            resp = self._access_nvi_api(
                token=token,
                params=params,
            )
            return self.fhir_mapper.from_fhir_bundle(resp)
        except Exception:
            logger.exception(
                "Failed to fetch referrals for subject: %s and source_id: %s",
                subject,
                source_id,
            )
            raise

    def _fetch_token(self, scope: str) -> AccessToken:
        try:
            return self.oauth_service.fetch_token(scope)
        except Exception:
            logger.exception("Failed to fetch access token for scope: %s", scope)
            raise

    def localize_referrals(self, subject: str) -> List[Referral]:
        token = self._fetch_token(scope="nvi:localize")
        referrals = self._query_referrals(token, subject)
        logger.info("Localized %d referrals: %s", len(referrals), referrals)
        return referrals

    def get_registered_referrals(
        self,
        subject: str,
    ) -> List[Referral]:
        token = self._fetch_token(scope="nvi:localize")
        referrals = self._query_referrals(token, subject, self.source_id)
        logger.info("Fetched %d referrals: %s", len(referrals), referrals)
        return referrals

    def add_referral(
        self,
        subject: str,
    ) -> Referral:
        list_res = self.fhir_mapper.to_list_resource(
            ura_number=self.org_registration_ura,
            subject=subject,
            source_id=self.source_id,
        )
        token = self._fetch_token(scope="nvi:create")
        resp = self._access_nvi_api(data=list_res, token=token)
        referral = self.fhir_mapper.from_list_resource(resp)
        logger.info("Updated NVI with referral: %s", referral)
        return referral

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
