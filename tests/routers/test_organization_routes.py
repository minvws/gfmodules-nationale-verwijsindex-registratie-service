import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fhir.resources.R4B.bundle import Bundle

from app.db.db import Database
from app.services.entity_services.organization_service import OrganizationService
from seeds.generate_data import DataGenerator
from tests.utils import add_organization, check_key_value


@pytest.mark.parametrize(
    "endpoint_suffix, expected_type",
    [
        ("/{id}", None),
        ("/_search", "searchset"),
        ("/_search/{id}", "searchset"),
        ("/_history", "history"),
        ("/{id}/_history", "history"),
    ],
)
def test_organization_routes(
    api_client: TestClient,
    org_endpoint: str,
    organization_service: OrganizationService,
    endpoint_suffix: str,
    expected_type: str | None,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    expected = add_organization(organization_service)
    endpoint = org_endpoint + endpoint_suffix.format(id=expected.fhir_id, ura=expected.ura_number)
    response = api_client.get(endpoint)
    assert response.status_code == 200
    data = response.json()
    if expected_type == "searchset" or expected_type == "history":
        assert data["total"] == 1
        assert data["type"] == expected_type
        assert check_key_value(data, "id", str(expected.fhir_id))
        bundle = Bundle(**data)
        assert isinstance(bundle, Bundle)
    else:
        assert check_key_value(data, "id", str(expected.fhir_id))


def test_delete_organization(
    api_client: TestClient,
    org_endpoint: str,
    organization_service: OrganizationService,
) -> None:
    expected = add_organization(organization_service)
    response = api_client.request("DELETE", f"{org_endpoint}/{expected.fhir_id}")
    assert response.status_code == 200


def test_update_organization(
    api_client: TestClient,
    org_endpoint: str,
    organization_service: OrganizationService,
) -> None:
    old = add_organization(organization_service)
    dg = DataGenerator()
    new_org = dg.generate_organization(ura_number=old.ura_number)
    new_org.id = str(old.fhir_id)  # type: ignore
    response = api_client.put(f"{org_endpoint}/{old.fhir_id}", json=dict(jsonable_encoder(new_org.dict())))
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == old.fhir_id.__str__()


def test_organization_history(
    api_client: TestClient,
    org_endpoint: str,
    organization_service: OrganizationService,
) -> None:
    org = add_organization(organization_service)
    response = api_client.request("GET", f"{org_endpoint}/{org.fhir_id}/_history")
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "history"
    assert data["entry"][0]["resource"] == org.data
    bundle = Bundle(**data)
    assert isinstance(bundle, Bundle)

    org_2 = add_organization(organization_service)
    response = api_client.request(
        "GET",
        f"{org_endpoint}/_history",  # Since creation of 2nd org
        params={"_since": org_2.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 1  # Only org_2 as it was created later than org 1
    assert bundle.entry[0].resource.id == org_2.fhir_id.__str__()  # type: ignore

    response = api_client.request(
        "GET",
        f"{org_endpoint}/_history",  # Since creation of 1st org
        params={"_since": org.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 2  # Both, because since is time of creation of first org
    assert bundle.entry[0].resource.id == org_2.fhir_id.__str__()  # type: ignore
    assert bundle.entry[1].resource.id == org.fhir_id.__str__()  # type: ignore


def test_organization_version(
    api_client: TestClient,
    org_endpoint: str,
    organization_service: OrganizationService,
) -> None:
    org = add_organization(organization_service)
    response = api_client.request("GET", f"{org_endpoint}/{org.fhir_id}/_history/{org.version}")
    assert response.status_code == 200
    data = response.json()
    assert org.data == data
    assert data["meta"]["versionId"] == org.version
