import inject

from app.config import get_config
from app.services.api.metadata_api_service import MetadataApiService
from app.services.api.nvi_api_service import NviApiService
from app.services.api.pseudonym_api_service import PseudonymApiService
from app.services.domain_map_service import DomainsMapService
from app.services.scheduler import Scheduler
from app.services.synchronizer import Synchronizer


def container_config(binder: inject.Binder) -> None:
    config = get_config()

    pseudonym_api_service = PseudonymApiService(
        endpoint=config.pseudonym_api.endpoint,
        timeout=config.pseudonym_api.timeout,
        mtls_cert=config.pseudonym_api.mtls_cert,
        mtls_key=config.pseudonym_api.mtls_key,
        mtls_ca=config.pseudonym_api.mtls_ca,
        provider_id=config.app.provider_id,
    )
    binder.bind(PseudonymApiService, pseudonym_api_service)

    nvi_api = NviApiService(
        endpoint=config.referral_api.endpoint,
        timeout=config.referral_api.timeout,
        mtls_cert=config.referral_api.mtls_cert,
        mtls_key=config.referral_api.mtls_key,
        mtls_ca=config.referral_api.mtls_ca,
    )
    binder.bind(NviApiService, nvi_api)

    metadata_api = MetadataApiService(
        endpoint=config.metadata_api.endpoint,
        timeout=config.metadata_api.timeout,
        mtls_cert=config.metadata_api.mtls_cert,
        mtls_key=config.metadata_api.mtls_key,
        mtls_ca=config.metadata_api.mtls_ca,
    )
    binder.bind(MetadataApiService, metadata_api)

    domain_map_service = DomainsMapService()

    synchronizer = Synchronizer(
        nvi_api=nvi_api,
        pseudonym_service=pseudonym_api_service,
        metadata_api=metadata_api,
        ura_number=config.app.ura_number,
        domains_map_service=domain_map_service,
    )
    binder.bind(Synchronizer, synchronizer)

    scheduler = Scheduler(function=synchronizer.synchronize_all_domains, delay=config.scheduler.scheduled_delay)
    binder.bind(Scheduler, scheduler)


def get_pseudonym_api_service() -> PseudonymApiService:
    return inject.instance(PseudonymApiService)


def get_nvi_api_service() -> NviApiService:
    return inject.instance(NviApiService)


def get_metadata_api_service() -> MetadataApiService:
    return inject.instance(MetadataApiService)


def get_synchronizer() -> Synchronizer:
    return inject.instance(Synchronizer)


def get_scheduler() -> Scheduler:
    return inject.instance(Scheduler)


def setup_container() -> None:
    inject.configure(container_config, once=True)
