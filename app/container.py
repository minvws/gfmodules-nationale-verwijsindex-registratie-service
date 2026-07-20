import inject

from app.config import get_config
from app.services.fhir.fhir_mapper import FhirMapper
from app.services.metadata import MetadataService
from app.services.nvi import NviService
from app.services.oauth.factory import create_oauth_classes
from app.services.pseudonym import PseudonymService
from app.services.registration.bundle import BundleRegistrationService
from app.services.registration.referrals import ReferralRegistrationService
from app.services.synchronization.domain_map import DomainsMapService
from app.services.synchronization.scheduler import Scheduler
from app.services.synchronization.synchronizer import Synchronizer


def container_config(binder: inject.Binder) -> None:
    config = get_config()

    nvi_oauth_service, prs_oauth_service = create_oauth_classes(config)

    pseudonym_service = PseudonymService(
        endpoint=config.pseudonym_api.endpoint,
        timeout=config.pseudonym_api.timeout,
        mtls_cert=config.pseudonym_api.mtls_cert,
        mtls_key=config.pseudonym_api.mtls_key,
        verify_ca=config.pseudonym_api.verify_ca,
        oauth_service=prs_oauth_service,
        extra_headers=config.overwrite_headers,
    )
    binder.bind(PseudonymService, pseudonym_service)

    fhir_mapper = FhirMapper(
        extension_identifier=config.nvi_fhir_systems.extension_identifier,
        extension_url=config.nvi_fhir_systems.extension_url,
        subject_system=config.nvi_fhir_systems.subject_system,
        source_system=config.nvi_fhir_systems.source_system,
    )
    binder.bind(FhirMapper, fhir_mapper)

    nvi_service = NviService(
        endpoint=config.referral_api.endpoint,
        timeout=config.referral_api.timeout,
        mtls_cert=config.referral_api.mtls_cert,
        mtls_key=config.referral_api.mtls_key,
        verify_ca=config.referral_api.verify_ca,
        oauth_service=nvi_oauth_service,
        fhir_mapper=fhir_mapper,
        source_id=config.app.source_id,
        org_registration_ura=config.app.org_registration_ura,
        extra_headers=config.overwrite_headers,
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
        nvi_oin=config.referral_api.nvi_oin,
    )
    binder.bind(ReferralRegistrationService, referral_registration_service)

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


def get_referral_registration_service() -> ReferralRegistrationService:
    return inject.instance(ReferralRegistrationService)


def get_metadata_service() -> MetadataService:
    return inject.instance(MetadataService)


def get_bundle_registration_service() -> BundleRegistrationService:
    return inject.instance(BundleRegistrationService)


def get_synchronizer() -> Synchronizer:
    return inject.instance(Synchronizer)


def get_scheduler() -> Scheduler:
    return inject.instance(Scheduler)


def setup_container() -> None:
    inject.configure(container_config, once=True)
