from typing import Generator

import inject
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application import create_fastapi_app
from app.config import get_config, set_config
from app.db.db import Database
from app.services.entity_services.endpoint_service import EndpointService
from app.services.entity_services.healthcare_service_service import (
    HealthcareServiceService,
)
from app.services.entity_services.location_service import LocationService
from app.services.entity_services.organization_affiliation_service import (
    OrganizationAffiliationService,
)
from app.services.entity_services.organization_service import OrganizationService
from app.services.entity_services.practitioner import PractitionerService
from app.services.entity_services.practitioner_role_service import PractitionerRoleService
from app.services.matching_care_service import MatchingCareService
from tests.test_config import (
    get_postgres_database,
    get_test_config,
    get_test_config_with_postgres_db_connection,
)


@pytest.fixture
def postgres_app() -> Generator[FastAPI, None, None]:
    set_config(get_test_config_with_postgres_db_connection())
    app = create_fastapi_app()
    yield app
    inject.clear()


@pytest.fixture
def sqlite_app() -> Generator[FastAPI, None, None]:
    set_config(get_test_config())
    app = create_fastapi_app()
    yield app
    inject.clear()


@pytest.fixture
def setup_postgres_database() -> Database:
    set_config(get_test_config_with_postgres_db_connection())
    try:
        # first use the database from the injector
        db = inject.instance(Database)
        db.truncate_tables()
        return db
    except inject.InjectorException:
        pass
    db = get_postgres_database()
    db.truncate_tables()
    return db


@pytest.fixture
def setup_sqlite_database() -> Database:
    set_config(get_test_config())
    try:
        # first use the database from the injector
        db = inject.instance(Database)
        return db
    except inject.InjectorException:
        pass
    db = Database(config=get_test_config().database)
    return db


@pytest.fixture
def api_client(postgres_app: FastAPI) -> TestClient:
    return TestClient(postgres_app)


@pytest.fixture
def sqlite_client(sqlite_app: FastAPI) -> TestClient:
    return TestClient(sqlite_app)


@pytest.fixture
def endpoint_service(setup_postgres_database: Database) -> EndpointService:
    return EndpointService(setup_postgres_database)


@pytest.fixture
def healthcareservice_service(
    setup_postgres_database: Database,
) -> HealthcareServiceService:
    return HealthcareServiceService(setup_postgres_database)


@pytest.fixture
def organization_service(setup_postgres_database: Database) -> OrganizationService:
    return OrganizationService(setup_postgres_database)


@pytest.fixture
def organization_affiliation_service(
    setup_postgres_database: Database,
) -> OrganizationAffiliationService:
    return OrganizationAffiliationService(setup_postgres_database)


@pytest.fixture
def location_service(setup_postgres_database: Database) -> LocationService:
    return LocationService(setup_postgres_database)


@pytest.fixture
def practitioner_service(
    setup_postgres_database: Database,
) -> PractitionerService:
    return PractitionerService(setup_postgres_database)


@pytest.fixture
def practitioner_role_service(
    setup_postgres_database: Database,
) -> PractitionerRoleService:
    return PractitionerRoleService(setup_postgres_database)


@pytest.fixture
def matching_care_service(
    organization_service: OrganizationService, endpoint_service: EndpointService
) -> MatchingCareService:
    return MatchingCareService(organization_service, endpoint_service)


@pytest.fixture
def org_endpoint() -> str:
    return "/Organization"


@pytest.fixture
def org_aff_endpoint() -> str:
    return "/OrganizationAffiliation"


@pytest.fixture
def practitioner_endpoint() -> str:
    return "/Practitioner"


@pytest.fixture
def practitioner_role_endpoint() -> str:
    return "/PractitionerRole"


@pytest.fixture
def endpoint_endpoint() -> str:
    return "/Endpoint"


@pytest.fixture
def healthcareservice_endpoint() -> str:
    return "/HealthcareService"


@pytest.fixture
def location_endpoint() -> str:
    return "/Location"


@pytest.fixture
def override_ura() -> Generator[None, None, None]:
    temp_test_config = get_config()

    """Context manager to temporarily update a part of the config and reset afterward."""
    try:
        temp_test_config.app.override_authentication_ura = "00000000"
        set_config(temp_test_config)
        yield None
    finally:
        # Revert to the original configuration
        temp_test_config.app.override_authentication_ura = None
        set_config(temp_test_config)
