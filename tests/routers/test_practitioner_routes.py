import uuid

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fhir.resources.R4B.bundle import Bundle

from app.db.db import Database
from app.services.entity_services.organization_service import OrganizationService
from app.services.entity_services.practitioner import (
    PractitionerService,
)
from seeds.generate_data import DataGenerator
from tests.utils import add_organization, add_practitioner, check_key_value


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
    practitioner_endpoint: str,
    practitioner_service: PractitionerService,
    endpoint_suffix: str,
    expected_type: str | None,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    expected = add_practitioner(practitioner_service)
    endpoint = practitioner_endpoint + endpoint_suffix.format(id=expected.fhir_id)
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
    practitioner_endpoint: str,
    practitioner_service: PractitionerService,
) -> None:
    expected = add_practitioner(practitioner_service)
    response = api_client.request("DELETE", f"{practitioner_endpoint}/{expected.fhir_id}")
    assert response.status_code == 204

    # Not found the second time
    response = api_client.request("DELETE", f"{practitioner_endpoint}/{expected.fhir_id}")
    assert response.status_code == 404


def test_update_organization_affiliation(
    api_client: TestClient,
    practitioner_endpoint: str,
    organization_service: OrganizationService,
    practitioner_service: PractitionerService,
) -> None:
    old_practitioner = add_practitioner(
        practitioner_service,
    )

    dg = DataGenerator()
    new_practitioner = dg.generate_practitioner()
    new_practitioner.id = str(old_practitioner.fhir_id)  # type: ignore
    response = api_client.put(
        f"{practitioner_endpoint}/{old_practitioner.fhir_id}",
        json=dict(jsonable_encoder(new_practitioner.dict())),
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == old_practitioner.fhir_id.__str__()
    assert response.headers["etag"] == 'W/"2"'


def test_practitioner_history(
    api_client: TestClient,
    practitioner_endpoint: str,
    practitioner_service: PractitionerService,
) -> None:
    practitioner = add_practitioner(practitioner_service)
    response = api_client.request("GET", f"{practitioner_endpoint}/{practitioner.fhir_id}/_history")
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "history"
    assert data["entry"][0]["resource"] == practitioner.data
    bundle = Bundle(**data)
    assert isinstance(bundle, Bundle)

    practitioner_2 = add_practitioner(practitioner_service)
    response = api_client.request(
        "GET",
        f"{practitioner_endpoint}/_history",  # Since creation of 2nd org
        params={"_since": practitioner_2.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 1  # Only practitioner_2 as it was created later than practitioner
    assert bundle.entry[0].resource.id == practitioner_2.fhir_id.__str__()  # type: ignore

    response = api_client.request(
        "GET",
        f"{practitioner_endpoint}/_history",  # Since creation of 1st org
        params={"_since": practitioner.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 2  # Both, because since is time of creation of first practitioner
    assert bundle.entry[0].resource.id == practitioner_2.fhir_id.__str__()  # type: ignore
    assert bundle.entry[1].resource.id == practitioner.fhir_id.__str__()  # type: ignore


def test_practitioner_version(
    api_client: TestClient,
    practitioner_endpoint: str,
    practitioner_service: PractitionerService,
) -> None:
    practitioner = add_practitioner(practitioner_service)
    response = api_client.request(
        "GET", f"{practitioner_endpoint}/{practitioner.fhir_id}/_history/{practitioner.version}"
    )
    assert response.status_code == 200
    data = response.json()
    assert practitioner.data == data
    assert data["meta"]["versionId"] == practitioner.version
    assert response.headers["etag"] == 'W/"1"'


def test_qualifation_checks(
    api_client: TestClient,
    practitioner_endpoint: str,
    practitioner_service: PractitionerService,
    organization_service: OrganizationService,
) -> None:
    # Create practitioner with existing qualification organization
    org = add_organization(organization_service)

    dg = DataGenerator()
    practitioner = dg.generate_practitioner(qualifications=[org.fhir_id])

    response = api_client.post(
        f"{practitioner_endpoint}",
        json=dict(jsonable_encoder(practitioner.dict())),
    )
    assert response.status_code == 201

    # Create practitioner without existing qualification organization
    practitioner = dg.generate_practitioner(qualifications=[uuid.UUID("11111111-2222-3333-4444-555555555555")])
    response = api_client.post(
        f"{practitioner_endpoint}",
        json=dict(jsonable_encoder(practitioner.dict())),
    )
    assert response.status_code == 404
    assert response.json()["detail"]["issue"][0]["code"] == "resource-not-found"
