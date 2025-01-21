from uuid import uuid4

from _pytest.python_api import raises
from fhir.resources.R4B.fhirtypes import String
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.organization import Organization as FhirOrganization

from app.db.db import Database
from app.exceptions.service_exceptions import (
    InvalidResourceException,
    ResourceNotDeletedException,
    ResourceNotFoundException,
)
from app.services.entity_services.endpoint_service import EndpointService
from app.services.entity_services.organization_service import OrganizationService
from seeds.generate_data import DataGenerator
from tests.utils import add_endpoint, add_organization


def test_get_one_correctly_finds_organization(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    expected = add_organization(organization_service)
    actual = organization_service.get_one(expected.fhir_id)
    assert actual.fhir_id == expected.fhir_id


def test_get_one_fails_correctly_when_no_organization_is_found(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    with raises(ResourceNotFoundException) as exc_info:
        organization_service.get_one(uuid4())
    assert "Organization not found" in exc_info.value.__str__()


def test_add_one_correctly_adds_organization(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    dg = DataGenerator()
    expected = dg.generate_organization()
    actual = organization_service.add_one(expected)
    assert actual.data.get("name") == expected.name  # type: ignore


def test_add_one_correctly_adds_organization_with_endpoint(
    organization_service: OrganizationService,
    endpoint_service: EndpointService,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    created_endpoint = add_endpoint(endpoint_service)
    dg = DataGenerator()
    expected = dg.generate_organization(endpoint_id=created_endpoint.fhir_id)
    actual = organization_service.add_one(expected)
    endpoints = actual.data.get("endpoint", [])  # type: ignore
    assert {"reference": f"Endpoint/{created_endpoint.fhir_id}"} in endpoints


def test_add_one_fails_correctly_when_endpoint_does_not_exist(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    fake_endpoint_id = uuid4()
    dg = DataGenerator()
    test_org = dg.generate_organization(endpoint_id=fake_endpoint_id)
    with raises(ResourceNotFoundException):
        organization_service.add_one(test_org)


def test_add_one_fails_correctly_with_invalid_resource(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    fake_endpoint_id = uuid4().__str__()
    dg = DataGenerator()
    test_org = dg.generate_organization()
    test_org.id = fake_endpoint_id  # type: ignore
    if not isinstance(test_org.identifier, list) or len(test_org.identifier) != 2:
        raise AssertionError
    test_org.identifier = [
        Identifier.construct(
            system="http://fhir.nl/fhir/NamingSystem/ura",  # type: ignore
            value="abc",
        )
    ]
    with raises(InvalidResourceException) as exc_info:
        organization_service.add_one(test_org)
    assert "URA number abc malformed:" in exc_info.value.__str__()
    test_org.identifier = []
    with raises(InvalidResourceException) as exc_info:
        organization_service.add_one(test_org)
    assert "URA number not found in organization resource" in exc_info.value.__str__()


def test_delete_one_correctly_deletes_organization(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    test_org = add_organization(organization_service)
    assert organization_service.get_one(test_org.fhir_id) is not None
    organization_service.delete_one(test_org.fhir_id)
    with raises(ResourceNotFoundException) as exc_info:
        organization_service.get_one(test_org.fhir_id)
    assert f"Organization not found for {test_org.fhir_id}" in exc_info.value.__str__()


def test_delete_one_organization_fails_when_endpoint_has_reference_to_it(
    organization_service: OrganizationService,
    endpoint_service: EndpointService,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    test_org = add_organization(organization_service)
    add_endpoint(endpoint_service, org_fhir_id=test_org.fhir_id)
    with raises(ResourceNotDeletedException):
        organization_service.delete_one(test_org.fhir_id)


def test_delete_one_correctly_fails_when_organization_is_not_found(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    with raises(ResourceNotFoundException) as exc_info:
        organization_service.delete_one(uuid4())
    assert "Organization not found" in exc_info.value.__str__()


def test_update_one_correctly_updates_organization(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    old_org = add_organization(organization_service, name="old_name")
    fhir_new_org = FhirOrganization(**old_org.data)  # type: ignore
    fhir_new_org.name = String("updated_name")
    updated_org = organization_service.update_one(old_org.fhir_id, fhir_new_org)
    assert old_org.fhir_id == updated_org.fhir_id
    assert old_org.data.get("name") == "old_name"  # type: ignore
    assert updated_org.data.get("name") == "updated_name"  # type: ignore


def test_update_one_correctly_adds_endpoint_to_organization(
    organization_service: OrganizationService,
    endpoint_service: EndpointService,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    old_org = add_organization(organization_service)
    fhir_new_org = FhirOrganization(**old_org.data)  # type: ignore
    test_endpoint = add_endpoint(endpoint_service)
    fhir_new_org.endpoint = [{"reference": f"Endpoint/{test_endpoint.fhir_id}"}]  # type: ignore
    updated_org = organization_service.update_one(old_org.fhir_id, fhir_new_org)
    assert old_org.fhir_id == updated_org.fhir_id
    endpoints = updated_org.data.get("endpoint", [])  # type: ignore
    assert {"reference": f"Endpoint/{test_endpoint.fhir_id}"} in endpoints

    fhir_new_org.identifier = [
        Identifier.construct(
            system="http://fhir.nl/fhir/NamingSystem/ura",  # type: ignore
            value="abc",
        )
    ]
    with raises(InvalidResourceException) as exc_info:
        organization_service.add_one(fhir_new_org)
    assert "URA number abc malformed:" in exc_info.value.__str__()
    fhir_new_org.identifier = []
    with raises(InvalidResourceException) as exc_info:
        organization_service.add_one(fhir_new_org)
    assert "URA number not found in organization resource" in exc_info.value.__str__()


def test_update_one_correctly_fails_when_endpoint_is_not_found(
    organization_service: OrganizationService, setup_postgres_database: Database
) -> None:
    setup_postgres_database.truncate_tables()
    old_org = add_organization(organization_service)
    fhir_new_org = FhirOrganization(**old_org.data)  # type: ignore
    random_endpoint_id = uuid4().__str__()
    fhir_new_org.endpoint = [{"reference": f"Endpoint/{random_endpoint_id}"}]  # type: ignore
    with raises(ResourceNotFoundException):
        organization_service.update_one(old_org.fhir_id, fhir_new_org)
