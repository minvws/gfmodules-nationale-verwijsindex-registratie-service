import uuid

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fhir.resources.R4B.bundle import Bundle

from app.db.db import Database
from app.services.entity_services.location_service import LocationService
from app.services.entity_services.organization_service import OrganizationService
from seeds.generate_data import DataGenerator
from tests.utils import add_location, add_organization, check_key_value


@pytest.mark.parametrize(
    "endpoint_suffix, expected_type",
    [
        ("/{id}", None),
        ("/_search", "searchset"),
        ("/_history", "history"),
        ("/{id}/_history", "history"),
    ],
)
def test_location_routes(
    api_client: TestClient,
    location_endpoint: str,
    location_service: LocationService,
    endpoint_suffix: str,
    expected_type: str | None,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    expected = add_location(location_service)
    endpoint = location_endpoint + endpoint_suffix.format(id=expected.fhir_id)
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


def test_delete_location(
    api_client: TestClient,
    location_endpoint: str,
    location_service: LocationService,
) -> None:
    expected = add_location(location_service)
    response = api_client.request("DELETE", f"{location_endpoint}/{expected.fhir_id}")
    assert response.status_code == 204

    # Not found the second time
    response = api_client.request("DELETE", f"{location_endpoint}/{expected.fhir_id}")
    assert response.status_code == 404


def test_update_location(
    api_client: TestClient,
    location_endpoint: str,
    organization_service: OrganizationService,
    location_service: LocationService,
) -> None:
    org1 = add_organization(organization_service)
    org2 = add_organization(organization_service)

    old_location_endpoint = add_location(
        location_service,
        organization=org1.fhir_id,
    )

    dg = DataGenerator()
    new_location_endpoint = dg.generate_location(organization=org2.fhir_id)
    new_location_endpoint.id = str(old_location_endpoint.fhir_id)  # type: ignore
    response = api_client.put(
        f"{location_endpoint}/{old_location_endpoint.fhir_id}",
        json=dict(jsonable_encoder(new_location_endpoint.dict())),
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == old_location_endpoint.fhir_id.__str__()
    assert response.headers["etag"] == 'W/"2"'


def test_location_history(
    api_client: TestClient,
    location_endpoint: str,
    location_service: LocationService,
) -> None:
    location = add_location(location_service)
    response = api_client.request("GET", f"{location_endpoint}/{location.fhir_id}/_history")
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "history"
    assert data["entry"][0]["resource"] == location.data
    bundle = Bundle(**data)
    assert isinstance(bundle, Bundle)

    location2 = add_location(location_service)
    response = api_client.request(
        "GET",
        f"{location_endpoint}/_history",  # Since creation of 2nd org
        params={"_since": location2.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 1  # Only location2 as it was created later than location
    assert bundle.entry[0].resource.id == location2.fhir_id.__str__()  # type: ignore

    response = api_client.request(
        "GET",
        f"{location_endpoint}/_history",  # Since creation of 1st org
        params={"_since": location.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 2  # Both, because since is time of creation of first location_endpoint
    assert bundle.entry[0].resource.id == location2.fhir_id.__str__()  # type: ignore
    assert bundle.entry[1].resource.id == location.fhir_id.__str__()  # type: ignore


def test_location_version(
    api_client: TestClient,
    location_endpoint: str,
    location_service: LocationService,
) -> None:
    location = add_location(location_service)
    response = api_client.request("GET", f"{location_endpoint}/{location.fhir_id}/_history/{location.version}")
    assert response.status_code == 200
    data = response.json()
    assert location.data == data
    assert data["meta"]["versionId"] == location.version
    assert response.headers["etag"] == 'W/"1"'


def test_create_location_with_non_existing_partof(
    api_client: TestClient,
    location_endpoint: str,
    location_service: LocationService,
) -> None:
    location1 = add_location(location_service)
    location2 = add_location(location_service, part_of=location1.fhir_id)
    assert location2.data["partOf"]["reference"] == "Location/" + location1.fhir_id.__str__()  # type: ignore

    try:
        # This should raise an exception as the partOf location does not exist
        add_location(location_service, part_of=uuid.UUID("850b6018-3537-4318-8e0d-aef286dc3c1b"))
    except Exception as e:
        assert "resource-not-found" in str(e)


def test_create_location_with_non_existing_organization(
    api_client: TestClient,
    location_endpoint: str,
    location_service: LocationService,
    organization_service: OrganizationService,
) -> None:
    org = add_organization(organization_service)
    location = add_location(location_service, organization=org.fhir_id)
    assert location.data["managingOrganization"]["reference"] == "Organization/" + org.fhir_id.__str__()  # type: ignore

    try:
        # This should raise an exception as there is not organization with this UUID
        add_location(location_service, organization=uuid.UUID("850b6018-3537-4318-8e0d-aef286dc3c1b"))
    except Exception as e:
        assert "resource-not-found" in str(e)
