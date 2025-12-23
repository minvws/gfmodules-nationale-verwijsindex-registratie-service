import logging
from datetime import datetime
from typing import Dict, List

from app.data import (
    OutcomeResponseSeverity,
    OutcomeResponseStatusCode,
)
from app.exceptions.fhir_exception import FHIRException
from app.models.bsn import BSN
from app.models.data_domain import DataDomain
from app.models.domains_map import DomainMapEntry, DomainsMap
from app.models.update_scheme import BsnUpdateScheme, UpdateScheme
from app.services.metadata import MetadataService
from app.services.registration.referrals import ReferralRegistrationService
from app.services.synchronization.domain_map import DomainsMapService

logger = logging.getLogger(__name__)


class Synchronizer:
    def __init__(
        self,
        registration_service: ReferralRegistrationService,
        metadata_api: MetadataService,
        domains_map_service: DomainsMapService,
    ) -> None:
        self._registration_service = registration_service
        self._metadata_api = metadata_api
        self._domain_map_service = domains_map_service
        self._last_run: str | None = None

    def get_allowed_domains(self) -> List[DataDomain]:
        return self._domain_map_service.get_domains()

    def _healthcheck_apis(self) -> Dict[str, bool]:
        logger.info("Checking health of APIs")
        return {
            "nvi_api": self._registration_service.nvi_service.server_healthy(),
            "pseudonym_api": self._registration_service.pseudonym_service.server_healthy(),
            "metadata_api": self._metadata_api.server_healthy(),
        }

    def synchronize_all_domains(self) -> Dict[str, List[UpdateScheme]]:
        return {
            k: v
            for domain in self._domain_map_service.get_domains()
            for k, v in self.synchronize_domain(domain).items()
        }

    def synchronize_domain(self, data_domain: DataDomain) -> Dict[str, List[UpdateScheme]]:
        data: Dict[str, List[UpdateScheme]] = {f"{data_domain}": []}
        logger.info(f"Synchronizing: {data_domain}")

        entry = self._domain_map_service.get_entry(data_domain)
        update_scheme = self.synchronize(data_domain, entry)
        data[data_domain.value].append(update_scheme)

        return data

    def synchronize(self, data_domain: DataDomain, domain_entry: DomainMapEntry) -> UpdateScheme:
        for health_status in self._healthcheck_apis().items():
            if not health_status[1]:
                msg = f"api {health_status[0]} health check failed"
                logger.warning(f"api {health_status[0]} health check failed")
                raise FHIRException(
                    status_code=OutcomeResponseStatusCode.INTERNAL_SERVER_ERROR.value,
                    severity=OutcomeResponseSeverity.ERROR.value,
                    code=OutcomeResponseSeverity.ERROR.value,
                    msg=msg,
                )

        bsn_update_scheme: List[BsnUpdateScheme] = []
        updated_bsns, latest_timestamp = self._metadata_api.get_update_scheme(
            data_domain, domain_entry.last_resource_update
        )

        for bsn in updated_bsns:
            new_referral = self._registration_service.register(BSN(bsn), data_domain)
            if new_referral is None:
                continue

            if latest_timestamp is not None and domain_entry.last_resource_update != latest_timestamp:
                logging.info(
                    f"Updating timestamp for resource {data_domain} from {domain_entry.last_resource_update} to {latest_timestamp}"
                )
                domain_entry.last_resource_update = latest_timestamp

            bsn_update_scheme.append(BsnUpdateScheme(bsn=bsn, referral=new_referral))

        self._last_run = datetime.now().isoformat()
        logging.info(f"last run {self._last_run}")
        return UpdateScheme(updated_data=bsn_update_scheme, domain_entry=domain_entry)

    def clear_cache(self, data_domain: DataDomain | None = None) -> DomainsMap:
        if data_domain is not None:
            return self._domain_map_service.clear_entry_timestamp(data_domain)

        return self._domain_map_service.clear_all_entries_timestamp()
