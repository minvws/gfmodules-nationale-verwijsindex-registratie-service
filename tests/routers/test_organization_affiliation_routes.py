import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fhir.resources.R4B.bundle import Bundle

from app.db.db import Database
from app.services.entity_services.organization_affiliation_service import (
    OrganizationAffiliationService,
)
from app.services.entity_services.organization_service import OrganizationService
from seeds.generate_data import DataGenerator
from tests.utils import add_organization, add_organization_affiliation, check_key_value


@pytest.mark.parametrize(
    "endpoint_suffix, expected_type",
    [
        ("/{id}", None),
        ("/_search", "searchset"),
        ("/_history", "history"),
        ("/{id}/_history", "history"),
    ],
)
def test_organization_routes(
    api_client: TestClient,
    org_aff_endpoint: str,
    organization_affiliation_service: OrganizationAffiliationService,
    endpoint_suffix: str,
    expected_type: str | None,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    expected = add_organization_affiliation(organization_affiliation_service)
    endpoint = org_aff_endpoint + endpoint_suffix.format(id=expected.fhir_id)
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


def test_delete_organization_affiliation(
    api_client: TestClient,
    org_aff_endpoint: str,
    organization_affiliation_service: OrganizationAffiliationService,
) -> None:
    expected = add_organization_affiliation(organization_affiliation_service)
    response = api_client.request("DELETE", f"{org_aff_endpoint}/{expected.fhir_id}")
    assert response.status_code == 204

    # Not found the second time
    response = api_client.request("DELETE", f"{org_aff_endpoint}/{expected.fhir_id}")
    assert response.status_code == 404


def test_update_organization_affiliation(
    api_client: TestClient,
    org_aff_endpoint: str,
    organization_service: OrganizationService,
    organization_affiliation_service: OrganizationAffiliationService,
) -> None:
    org1 = add_organization(organization_service)
    org2 = add_organization(organization_service)

    old_org_aff = add_organization_affiliation(
        organization_affiliation_service,
        organization=org1.fhir_id,
    )

    dg = DataGenerator()
    new_org_aff = dg.generate_organization_affiliation(
        organization=org1.fhir_id, participation_organization=org2.fhir_id, active=True
    )
    new_org_aff.id = str(old_org_aff.fhir_id)  # type: ignore
    response = api_client.put(
        f"{org_aff_endpoint}/{old_org_aff.fhir_id}",
        json=dict(jsonable_encoder(new_org_aff.dict())),
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == old_org_aff.fhir_id.__str__()
    assert response.headers["etag"] == 'W/"2"'


def test_organization_affiliation_history(
    api_client: TestClient,
    org_aff_endpoint: str,
    organization_affiliation_service: OrganizationAffiliationService,
) -> None:
    org_aff = add_organization_affiliation(organization_affiliation_service)
    response = api_client.request("GET", f"{org_aff_endpoint}/{org_aff.fhir_id}/_history")
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "history"
    assert data["entry"][0]["resource"] == org_aff.data
    bundle = Bundle(**data)
    assert isinstance(bundle, Bundle)

    org_aff_2 = add_organization_affiliation(organization_affiliation_service)
    response = api_client.request(
        "GET",
        f"{org_aff_endpoint}/_history",  # Since creation of 2nd org
        params={"_since": org_aff_2.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 1  # Only org_aff_2 as it was created later than org_aff
    assert bundle.entry[0].resource.id == org_aff_2.fhir_id.__str__()  # type: ignore

    response = api_client.request(
        "GET",
        f"{org_aff_endpoint}/_history",  # Since creation of 1st org
        params={"_since": org_aff.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 2  # Both, because since is time of creation of first org_aff
    assert bundle.entry[0].resource.id == org_aff_2.fhir_id.__str__()  # type: ignore
    assert bundle.entry[1].resource.id == org_aff.fhir_id.__str__()  # type: ignore


def test_organization_affiliation_version(
    api_client: TestClient,
    org_aff_endpoint: str,
    organization_affiliation_service: OrganizationAffiliationService,
) -> None:
    org_aff = add_organization_affiliation(organization_affiliation_service)
    response = api_client.request("GET", f"{org_aff_endpoint}/{org_aff.fhir_id}/_history/{org_aff.version}")
    assert response.status_code == 200
    data = response.json()
    assert org_aff.data == data
    assert data["meta"]["versionId"] == org_aff.version
    assert response.headers["etag"] == 'W/"1"'
