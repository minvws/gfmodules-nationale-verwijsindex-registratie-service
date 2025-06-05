import logging
from datetime import datetime
from typing import Dict, List

from app.data import BSN, DataDomain
from app.models.domains_map import DomainMapEntry, DomainsMap
from app.models.pseudonym import PseudonymCreateDto
from app.models.referrals import CreateReferralDTO, ReferralQueryDTO
from app.models.update_scheme import BsnUpdateScheme, UpdateScheme
from app.services.api.metadata_api_service import MetadataApiService
from app.services.api.nvi_api_service import NviApiService
from app.services.api.pseudonym_api_service import PseudonymApiService
from app.services.domain_map_service import DomainsMapService

logger = logging.getLogger(__name__)


class Synchronizer:
    def __init__(
        self,
        nvi_api: NviApiService,
        pseudonym_service: PseudonymApiService,
        metadata_api: MetadataApiService,
        domains_map_service: DomainsMapService,
        ura_number: str,
    ) -> None:
        self.__nvi_api = nvi_api
        self.__pseudonym_service = pseudonym_service
        self.__metadata_api = metadata_api
        self.__domains_map_service = domains_map_service
        self.__ura_number = ura_number
        self.__last_run: str | None = None

    def _healthcheck_apis(self) -> Dict[str, bool]:
        logger.info("Checking health of APIs")
        return {
            "nvi_api": self.__nvi_api.api_healthy(),
            "metadata_api": self.__metadata_api.api_healthy(),
            "pseudonym_service": self.__pseudonym_service.api_healthy(),
        }

    def synchronize_all_domains(self) -> Dict[str, List[UpdateScheme]]:
        for health_status in self._healthcheck_apis().items():
            if not health_status[1]:
                logger.warning(f"API {health_status[0]} health check failed")
                raise Exception(f"API {health_status[0]} health check failed")
        return {
            k: v
            for domain in self.__domains_map_service.get_domains()
            for k, v in self.synchronize_domain(domain).items()
        }

    def synchronize_domain(self, data_domain: DataDomain) -> Dict[str, List[UpdateScheme]]:
        for health_status in self._healthcheck_apis().items():
            if not health_status[1]:
                logger.warning(f"API {health_status[0]} health check failed")
                raise Exception(f"API {health_status[0]} health check failed")
        data: Dict[str, List[UpdateScheme]] = {f"{data_domain}": []}
        logger.info(f"Synchronizing: {data_domain}")
        for entry in self.__domains_map_service.get_entries(data_domain):
            logger.info(f"Updating resource: {entry.resource_type}")
            update_scheme = self.synchronize(data_domain, entry)
            data[str(data_domain)].append(update_scheme)
        return data

    def synchronize(self, data_domain: DataDomain, domain_entry: DomainMapEntry) -> UpdateScheme:
        bsn_update_scheme: List[BsnUpdateScheme] = []
        updated_bsns, latest_timestamp = self.__metadata_api.get_update_scheme(
            domain_entry.resource_type, domain_entry.last_resource_update
        )

        for bsn in updated_bsns:
            pseudonym = self.__pseudonym_service.submit(PseudonymCreateDto(bsn=BSN(bsn)))
            referral = self.__nvi_api.get_referrals(
                ReferralQueryDTO(
                    pseudonym=str(pseudonym),
                    data_domain=str(data_domain),
                    ura_number=self.__ura_number,
                )
            )
            if referral is not None:
                continue

            new_referal = self.__nvi_api.submit(
                CreateReferralDTO(
                    ura_number=self.__ura_number,
                    pseudonym=str(pseudonym),
                    data_domain=str(data_domain),
                    requesting_uzi_number=self.__ura_number,
                )
            )
            if latest_timestamp is not None and domain_entry.last_resource_update != latest_timestamp:
                logging.info(
                    f"Updating timestamp for resource {domain_entry.resource_type} from {domain_entry.last_resource_update} to {latest_timestamp}"
                )
                domain_entry.last_resource_update = latest_timestamp

            bsn_update_scheme.append(BsnUpdateScheme(bsn=bsn, referral=new_referal))

        self.__last_run = datetime.now().isoformat()
        logging.info(f"last run {self.__last_run}")
        return UpdateScheme(updated_data=bsn_update_scheme, domain_entry=domain_entry)

    def clear_cache(self, data_domain: DataDomain | None = None) -> DomainsMap:
        if data_domain is not None:
            return self.__domains_map_service.clear_entries_timestamp(data_domain)

        return self.__domains_map_service.clear_all_entries_timestamp()
