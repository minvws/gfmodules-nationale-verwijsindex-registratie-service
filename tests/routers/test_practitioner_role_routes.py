import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fhir.resources.R4B.bundle import Bundle

from app.db.db import Database
from app.services.entity_services.organization_service import OrganizationService
from app.services.entity_services.practitioner_role_service import (
    PractitionerRoleService,
)
from seeds.generate_data import DataGenerator
from tests.utils import add_organization, add_practitioner_role, check_key_value


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
    practitioner_role_endpoint: str,
    practitioner_role_service: PractitionerRoleService,
    endpoint_suffix: str,
    expected_type: str | None,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    expected = add_practitioner_role(practitioner_role_service)
    endpoint = practitioner_role_endpoint + endpoint_suffix.format(id=expected.fhir_id)
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


def test_delete_practitioner_role(
    api_client: TestClient,
    practitioner_role_endpoint: str,
    practitioner_role_service: PractitionerRoleService,
) -> None:
    expected = add_practitioner_role(practitioner_role_service)
    response = api_client.request("DELETE", f"{practitioner_role_endpoint}/{expected.fhir_id}")
    assert response.status_code == 204

    # Not found the second time
    response = api_client.request("DELETE", f"{practitioner_role_endpoint}/{expected.fhir_id}")
    assert response.status_code == 404


def test_update_practitioner_role(
    api_client: TestClient,
    practitioner_role_endpoint: str,
    organization_service: OrganizationService,
    practitioner_role_service: PractitionerRoleService,
) -> None:
    org1 = add_organization(organization_service)
    org2 = add_organization(organization_service)

    old_role = add_practitioner_role(
        practitioner_role_service,
        organization=org1.fhir_id,
    )

    dg = DataGenerator()
    new_role = dg.generate_practitioner_role(
        id=old_role.fhir_id,
        organization=org2.fhir_id,
    )
    response = api_client.put(
        f"{practitioner_role_endpoint}/{old_role.fhir_id}",
        json=dict(jsonable_encoder(new_role.dict())),
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == old_role.fhir_id.__str__()
    assert response.headers["etag"] == 'W/"2"'


def test_practitioner_role_history(
    api_client: TestClient,
    practitioner_role_endpoint: str,
    practitioner_role_service: PractitionerRoleService,
) -> None:
    org_aff = add_practitioner_role(practitioner_role_service)
    response = api_client.request("GET", f"{practitioner_role_endpoint}/{org_aff.fhir_id}/_history")
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "history"
    assert data["entry"][0]["resource"] == org_aff.data
    bundle = Bundle(**data)
    assert isinstance(bundle, Bundle)

    org_aff_2 = add_practitioner_role(practitioner_role_service)
    response = api_client.request(
        "GET",
        f"{practitioner_role_endpoint}/_history",  # Since creation of 2nd org
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
        f"{practitioner_role_endpoint}/_history",  # Since creation of 1st org
        params={"_since": org_aff.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 2  # Both, because since is time of creation of first org_aff
    assert bundle.entry[0].resource.id == org_aff_2.fhir_id.__str__()  # type: ignore
    assert bundle.entry[1].resource.id == org_aff.fhir_id.__str__()  # type: ignore


def test_practitioner_role_version(
    api_client: TestClient,
    practitioner_role_endpoint: str,
    practitioner_role_service: PractitionerRoleService,
) -> None:
    org_aff = add_practitioner_role(practitioner_role_service)
    response = api_client.request("GET", f"{practitioner_role_endpoint}/{org_aff.fhir_id}/_history/{org_aff.version}")
    assert response.status_code == 200
    data = response.json()
    assert org_aff.data == data
    assert data["meta"]["versionId"] == org_aff.version
    assert response.headers["etag"] == 'W/"1"'
