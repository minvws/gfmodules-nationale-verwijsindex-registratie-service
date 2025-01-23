import inject

from app.config import get_config
from app.services.pseudonym_service import PseudonymService
from app.services.referral_service import ReferralService


def container_config(binder: inject.Binder) -> None:
    config = get_config()
    provider_id = config.app.provider_id

    referral_service = ReferralService(
        endpoint=config.referral_api.endpoint,
        timeout=config.referral_api.timeout,
        mtls_cert=config.referral_api.mtls_cert,
        mtls_key=config.referral_api.mtls_key,
        mtls_ca=config.referral_api.mtls_ca,
    )
    binder.bind(ReferralService, referral_service)

    pseudonym_service = PseudonymService(
        endpoint=config.pseudonym_api.endpoint,
        timeout=config.pseudonym_api.timeout,
        provider_id=provider_id,
        mtls_cert=config.pseudonym_api.mtls_cert,
        mtls_key=config.pseudonym_api.mtls_key,
        mtls_ca=config.pseudonym_api.mtls_ca,
    )
    binder.bind(PseudonymService, pseudonym_service)


def get_pseudonym_service() -> PseudonymService:
    return inject.instance(PseudonymService)


def get_referral_service() -> ReferralService:
    return inject.instance(ReferralService)


def setup_container() -> None:
    inject.configure(container_config, once=True)
