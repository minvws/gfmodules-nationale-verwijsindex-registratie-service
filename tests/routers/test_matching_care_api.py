from fastapi.testclient import TestClient
from fhir.resources.R4B.bundle import Bundle

from app.db.db import Database
from app.services.entity_services.endpoint_service import EndpointService
from app.services.entity_services.organization_service import OrganizationService
from tests.utils import add_endpoint, add_organization, check_key_value


def test_organization_returns_fhir_bundle(api_client: TestClient, org_endpoint: str) -> None:
    response = api_client.get(f"{org_endpoint}/_search")
    assert response.status_code == 200
    bundle = Bundle.parse_raw(response.text)
    assert isinstance(bundle, Bundle)


def test_organization_returns_correct_organization(
    api_client: TestClient,
    org_endpoint: str,
    organization_service: OrganizationService,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()

    expected_org = add_organization(organization_service)
    response = api_client.get(f"{org_endpoint}/_search")
    assert response.status_code == 200
    bundle = Bundle.parse_raw(response.text)
    assert isinstance(bundle, Bundle)
    assert check_key_value(response.json(), "id", str(expected_org.fhir_id))


def test_organization_returns_422(api_client: TestClient, org_endpoint: str) -> None:
    response = api_client.get(f"{org_endpoint}/_search", params="_id=0")
    assert response.status_code == 422


def test_endpoint_returns_fhir_bundle(api_client: TestClient, endpoint_endpoint: str) -> None:
    response = api_client.get(f"{endpoint_endpoint}/_search")
    assert response.status_code == 200
    bundle = Bundle.parse_raw(response.text)
    assert isinstance(bundle, Bundle)


def test_endpoint_returns_correct_endpoint(
    api_client: TestClient,
    endpoint_endpoint: str,
    endpoint_service: EndpointService,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    expected_endpoint = add_endpoint(endpoint_service)
    response = api_client.get(f"{endpoint_endpoint}/_search")
    assert response.status_code == 200
    bundle = Bundle.parse_raw(response.text)
    assert isinstance(bundle, Bundle)
    assert check_key_value(response.json(), "id", str(expected_endpoint.fhir_id))


def test_endpoint_returns_422(api_client: TestClient, endpoint_endpoint: str) -> None:
    response = api_client.get(f"{endpoint_endpoint}/_search", params="_id=0")
    assert response.status_code == 422
