import inject

from app.config import get_config
from app.services.api.metadata_api_service import MetadataApiService
from app.services.domain_map_service import DomainsMapService
from app.services.metadata import MetadataService
from app.services.nvi import NviService
from app.services.pseudonym import PseudonymService
from app.services.scheduler import Scheduler
from app.services.synchronizer import Synchronizer


def container_config(binder: inject.Binder) -> None:
    config = get_config()

    pseudonym_service = PseudonymService(
        endpoint=config.pseudonym_api.endpoint,
        timeout=config.pseudonym_api.timeout,
        mtls_cert=config.pseudonym_api.mtls_cert,
        mtls_key=config.pseudonym_api.mtls_key,
        mtls_ca=config.pseudonym_api.mtls_ca,
        provider_id=config.app.provider_id,
    )
    binder.bind(PseudonymService, pseudonym_service)

    nvi_service = NviService(
        endpoint=config.referral_api.endpoint,
        timeout=config.referral_api.timeout,
        mtls_cert=config.referral_api.mtls_cert,
        mtls_key=config.referral_api.mtls_key,
        mtls_ca=config.referral_api.mtls_ca,
    )
    binder.bind(NviService, nvi_service)

    metadata_service = MetadataService(
        endpoint=config.metadata_api.endpoint,
        timeout=config.metadata_api.timeout,
        mtls_cert=config.metadata_api.mtls_cert,
        mtls_key=config.metadata_api.mtls_key,
        mtls_ca=config.metadata_api.mtls_ca,
    )
    binder.bind(MetadataApiService, metadata_service)

    domain_map_service = DomainsMapService()

    synchronizer = Synchronizer(
        nvi_api=nvi_service,
        pseudonym_api=pseudonym_service,
        metadata_api=metadata_service,
        ura_number=config.app.ura_number,
        domains_map_service=domain_map_service,
    )
    binder.bind(Synchronizer, synchronizer)

    scheduler = Scheduler(
        function=synchronizer.synchronize_all_domains,
        delay=config.scheduler.scheduled_delay,
    )
    binder.bind(Scheduler, scheduler)


def get_pseudonym_api_service() -> PseudonymService:
    return inject.instance(PseudonymService)


def get_nvi_api_service() -> NviService:
    return inject.instance(NviService)


def get_metadata_api_service() -> MetadataApiService:
    return inject.instance(MetadataApiService)


def get_synchronizer() -> Synchronizer:
    return inject.instance(Synchronizer)


def get_scheduler() -> Scheduler:
    return inject.instance(Scheduler)


def setup_container() -> None:
    inject.configure(container_config, once=True)
