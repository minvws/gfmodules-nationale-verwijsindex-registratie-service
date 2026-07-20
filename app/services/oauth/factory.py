from typing import Tuple

from app.config import Config
from app.services.oauth.oauth_service import OauthService


def create_oauth_classes(config: Config) -> Tuple[OauthService, OauthService]:
    oauth_conf = config.oauth_api
    nvi_oauth = OauthService(
        endpoint=oauth_conf.nvi_endpoint,
        timeout=oauth_conf.timeout,
        mock=oauth_conf.mock,
        mtls_cert=oauth_conf.mtls_cert,
        mtls_key=oauth_conf.mtls_key,
        verify_ca=oauth_conf.verify_ca,
        org_register_id=config.app.org_registration_ura,
        source_id=config.app.source_id,
        target_audience=oauth_conf.nvi_audience,
        client_oin=config.app.client_oin,
        client_common_name=config.app.client_common_name,
    )
    prs_oauth = OauthService(
        endpoint=oauth_conf.prs_endpoint,
        timeout=oauth_conf.timeout,
        mock=oauth_conf.mock,
        mtls_cert=oauth_conf.mtls_cert,
        mtls_key=oauth_conf.mtls_key,
        verify_ca=oauth_conf.verify_ca,
        org_register_id=config.app.org_registration_oin,
        target_audience=oauth_conf.prs_audience,
        client_oin=config.app.client_oin,
        client_common_name=config.app.client_common_name,
    )
    return nvi_oauth, prs_oauth
