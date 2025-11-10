import inject

from app.config import get_config
from app.models.ura_number import UraNumber
from app.services.authorization_check_service import AuthorizationCheckService
from app.services.metadata import MetadataService
from app.services.nvi import NviService
from app.services.OtvService.factory import create_otv_service
from app.services.OtvService.get_otv_ura import get_otv_ura
from app.services.OtvService.interface import OtvService
from app.services.pseudonym import PseudonymService
from app.services.registration.bundle import BundleRegistartionService
from app.services.registration.referrals import ReferralRegistrationService
from app.services.synchronization.domain_map import DomainsMapService
from app.services.synchronization.scheduler import Scheduler
from app.services.synchronization.synchronizer import Synchronizer
from app.services.ura import UraNumberService


def container_config(binder: inject.Binder) -> None:
    config = get_config()

    ura_number = UraNumberService.get_ura_number(config)
    binder.bind(UraNumber, ura_number)

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
    binder.bind(MetadataService, metadata_service)

    referral_registration_service = ReferralRegistrationService(
        nvi_service=nvi_service,
        pseudonym_service=pseudonym_service,
        ura_number=ura_number.value,
    )

    otv_service = create_otv_service(config.otv_stub_api)
    binder.bind(OtvService, otv_service)

    authorization_check_service = AuthorizationCheckService(
        metadata_service=metadata_service,
        otv_service=otv_service,
        pseudonym_service=pseudonym_service,
        otv_ura=get_otv_ura(config.otv_stub_certificate),
    )
    binder.bind(AuthorizationCheckService, authorization_check_service)

    bundle_registration_service = BundleRegistartionService(referrals_service=referral_registration_service)
    binder.bind(BundleRegistartionService, bundle_registration_service)

    domain_map_service = DomainsMapService(data_domains=config.app.data_domains)

    synchronizer = Synchronizer(
        registration_service=referral_registration_service,
        metadata_api=metadata_service,
        domains_map_service=domain_map_service,
    )
    binder.bind(Synchronizer, synchronizer)

    scheduler = Scheduler(
        function=synchronizer.synchronize_all_domains,
        delay=config.scheduler.scheduled_delay,
    )
    binder.bind(Scheduler, scheduler)


def get_authorization_check_service() -> AuthorizationCheckService:
    return inject.instance(AuthorizationCheckService)


def get_otv_service() -> OtvService:
    instance = inject.instance(OtvService)
    assert isinstance(instance, OtvService)
    return instance


def get_pseudonym_service() -> PseudonymService:
    return inject.instance(PseudonymService)


def get_nvi_service() -> NviService:
    return inject.instance(NviService)


def get_metadata_service() -> MetadataService:
    return inject.instance(MetadataService)


def get_bundle_registration_service() -> BundleRegistartionService:
    return inject.instance(BundleRegistartionService)


def get_synchronizer() -> Synchronizer:
    return inject.instance(Synchronizer)


def get_scheduler() -> Scheduler:
    return inject.instance(Scheduler)


def get_ura_number() -> UraNumber:
    return inject.instance(UraNumber)


def setup_container() -> None:
    inject.configure(container_config, once=True)
