import inject

from app.config import get_config
from app.models.ura_number import UraNumber
from app.services.api.oauth import OauthService
from app.services.fhir.nvi_data_reference import NviDataReferenceMapper
from app.services.metadata import MetadataService
from app.services.nvi import NviService
from app.services.pseudonym import PseudonymService
from app.services.registration.bundle import BundleRegistrationService
from app.services.registration.referrals import ReferralRegistrationService
from app.services.synchronization.domain_map import DomainsMapService
from app.services.synchronization.scheduler import Scheduler
from app.services.synchronization.synchronizer import Synchronizer
from app.services.ura import UraNumberService


def container_config(binder: inject.Binder) -> None:
    config = get_config()

    ura_number = UraNumberService.get_ura_number_from_config(config)
    binder.bind(UraNumber, ura_number)

    pseudonym_service = PseudonymService(
        endpoint=config.pseudonym_api.endpoint,
        timeout=config.pseudonym_api.timeout,
        mtls_cert=config.pseudonym_api.mtls_cert,
        mtls_key=config.pseudonym_api.mtls_key,
        verify_ca=config.pseudonym_api.verify_ca,
        provider_id=config.app.provider_id,
    )
    binder.bind(PseudonymService, pseudonym_service)

    nvi_data_reference_mapper = NviDataReferenceMapper(
        pseudonym_system=config.nvi_fhir_systems.pseudonym_system,
        source_system=config.nvi_fhir_systems.source_system,
        organization_type_system=config.nvi_fhir_systems.organization_type_system,
        care_context_system=config.nvi_fhir_systems.care_context_system,
    )
    binder.bind(NviDataReferenceMapper, nvi_data_reference_mapper)

    oauth_service = OauthService(
        endpoint=config.oauth_api.endpoint,
        timeout=config.oauth_api.timeout,
        mtls_cert=config.oauth_api.mtls_cert,
        mtls_key=config.oauth_api.mtls_key,
        verify_ca=config.oauth_api.verify_ca,
        mock=config.oauth_api.mock,
    )

    nvi_service = NviService(
        endpoint=config.referral_api.endpoint,
        timeout=config.referral_api.timeout,
        mtls_cert=config.referral_api.mtls_cert,
        mtls_key=config.referral_api.mtls_key,
        verify_ca=config.referral_api.verify_ca,
        oauth_service=oauth_service,
        fhir_mapper=nvi_data_reference_mapper,
        oauth_target_audience=config.referral_api.oauth_target_audience,
    )
    binder.bind(NviService, nvi_service)

    metadata_service = MetadataService(
        endpoint=config.metadata_api.endpoint,
        timeout=config.metadata_api.timeout,
        mtls_cert=config.metadata_api.mtls_cert,
        mtls_key=config.metadata_api.mtls_key,
        verify_ca=config.metadata_api.verify_ca,
    )
    binder.bind(MetadataService, metadata_service)

    referral_registration_service = ReferralRegistrationService(
        nvi_service=nvi_service,
        pseudonym_service=pseudonym_service,
        ura_number=ura_number,
        default_organization_type=config.app.default_organization_type,
        nvi_ura_number=UraNumber(config.referral_api.nvi_ura_number),
    )

    bundle_registration_service = BundleRegistrationService(referrals_service=referral_registration_service)
    binder.bind(BundleRegistrationService, bundle_registration_service)

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


def get_pseudonym_service() -> PseudonymService:
    return inject.instance(PseudonymService)


def get_nvi_service() -> NviService:
    return inject.instance(NviService)


def get_metadata_service() -> MetadataService:
    return inject.instance(MetadataService)


def get_bundle_registration_service() -> BundleRegistrationService:
    return inject.instance(BundleRegistrationService)


def get_synchronizer() -> Synchronizer:
    return inject.instance(Synchronizer)


def get_scheduler() -> Scheduler:
    return inject.instance(Scheduler)


def get_ura_number() -> UraNumber:
    return inject.instance(UraNumber)


def setup_container() -> None:
    inject.configure(container_config, once=True)
