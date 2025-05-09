import inject

from app.config import get_config
from app.services.api.metadata_api_service import MetadataApiService
from app.services.api.nvi_api_service import NviApiService
from app.services.domain_map_service import DomainsMapService
from app.services.pseudonym_service import PseudonymService
from app.services.referral_service import ReferralService
from app.services.scheduler import Scheduler
from app.services.synchronizer import Synchronizer
from app.utils import create_domains_map


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

    nv_api = NviApiService(url=config.app.nvi_url)
    metadata_api = MetadataApiService(url=config.app.metadata_url)
    domain_map_service = DomainsMapService(domains_map=create_domains_map(config.app.domains_map_json_path))

    synchronizer = Synchronizer(
        nvi_api=nv_api,
        pseudonym_service=pseudonym_service,
        metadata_api=metadata_api,
        ura_number=config.app.ura_number,
        domains_map_service=domain_map_service,
    )
    binder.bind(Synchronizer, synchronizer)

    scheduler = Scheduler(function=synchronizer.synchronize_all_domains, delay=config.app.scheduled_delay)
    binder.bind(Scheduler, scheduler)


def get_pseudonym_service() -> PseudonymService:
    return inject.instance(PseudonymService)


def get_referral_service() -> ReferralService:
    return inject.instance(ReferralService)


def get_synchronizer() -> Synchronizer:
    return inject.instance(Synchronizer)


def get_scheduler() -> Scheduler:
    return inject.instance(Scheduler)


def setup_container() -> None:
    inject.configure(container_config, once=True)
