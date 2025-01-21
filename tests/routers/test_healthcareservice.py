import uuid
from uuid import UUID

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fhir.resources.R4B.bundle import Bundle

from app.db.db import Database
from app.db.entities.healthcare_service.healthcare_service import HealthcareService
from app.exceptions.service_exceptions import ResourceNotFoundException
from app.services.entity_services.healthcare_service_service import (
    HealthcareServiceService,
)
from seeds.generate_data import DataGenerator
from tests.utils import check_key_value


@pytest.mark.parametrize(
    "url_suffix, expected_type",
    [
        ("/_search", "searchset"),
    ],
)
def test_healthcareservice_routes(
    api_client: TestClient,
    healthcareservice_endpoint: str,
    healthcareservice_service: HealthcareServiceService,
    url_suffix: str,
    expected_type: str | None,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()

    expected = generate_entity(uuid.UUID("2f6c9432-a495-4112-be1b-134bc4656f1f"), healthcareservice_service)
    url_endpoint = healthcareservice_endpoint + url_suffix.format(id=expected.id)
    response = api_client.get(url_endpoint)

    assert response.status_code == 200
    data = response.json()
    if expected_type == "searchset":
        assert data["total"] == 1
        assert data["type"] == expected_type
        assert check_key_value(data, "id", str(expected.fhir_id))
        bundle = Bundle.parse_raw(response.text)
        assert isinstance(bundle, Bundle)
    else:
        assert check_key_value(data, "id", str(expected.fhir_id))


def test_delete_endpoint(
    api_client: TestClient,
    healthcareservice_endpoint: str,
    healthcareservice_service: HealthcareServiceService,
) -> None:
    expected = generate_entity(uuid.UUID("8235f9d5-1d03-4b37-b5fd-a69cdb2dc940"), healthcareservice_service)

    response = api_client.request("DELETE", f"{healthcareservice_endpoint}/{expected.fhir_id}")
    assert response.status_code == 204

    # Next delete attempt should return 404
    response = api_client.request("DELETE", f"{healthcareservice_endpoint}/{expected.fhir_id}")
    assert response.status_code == 404


def test_update_endpoint(
    api_client: TestClient,
    healthcareservice_endpoint: str,
    healthcareservice_service: HealthcareServiceService,
) -> None:
    # Insert first version
    fhir_entity = generate_entity(
        uuid.UUID("57d03d8b-3d32-46e1-8eba-e24fe11cbf42"),
        healthcareservice_service,
        "initial comment",
    )

    fhir_entity.data["comment"] = "Updated comment"  # type: ignore
    response = api_client.put(
        f"{healthcareservice_endpoint}/{str(fhir_entity.fhir_id)}",
        json=jsonable_encoder(fhir_entity.data),
    )

    # Check response of the update
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == str(fhir_entity.fhir_id)
    assert response.headers["etag"] == 'W/"2"'

    # Next update will trigger version 3
    fhir_entity.data["comment"] = "Newer updated comment"  # type: ignore
    response = api_client.put(
        f"{healthcareservice_endpoint}/{str(fhir_entity.fhir_id)}",
        json=dict(jsonable_encoder(fhir_entity.data)),
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == str(fhir_entity.fhir_id)
    assert response.headers["etag"] == 'W/"3"'

    # New entry with different ID triggers just a new entry with version 1
    new_entity = generate_entity(uuid.UUID("455a4011-d553-4166-be9f-043f4ff5bea2"), healthcareservice_service)
    new_entity.comment = "New element"  # type: ignore
    response = api_client.put(
        f"{healthcareservice_endpoint}/{str(new_entity.fhir_id)}",
        json=dict(jsonable_encoder(new_entity.data)),
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == str(new_entity.fhir_id)
    assert updated_data["id"] != str(fhir_entity.fhir_id)
    assert response.headers["etag"] == 'W/"1"'


def test_history_endpoint(
    api_client: TestClient,
    healthcareservice_endpoint: str,
    healthcareservice_service: HealthcareServiceService,
) -> None:
    id = uuid.UUID("4fce820d-e890-4459-ac7f-0df8f0da2b49")
    generate_entity(id, healthcareservice_service, comment="First version")
    generate_entity(id, healthcareservice_service, comment="Second version")
    generate_entity(id, healthcareservice_service, comment="Third version")

    response = api_client.request("GET", f"{healthcareservice_endpoint}/{str(id)}/_history")
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "history"
    assert data["entry"][2]["fullUrl"].endswith("/_history/1")
    assert data["entry"][2]["resource"]["comment"] == "First version"
    assert data["entry"][1]["fullUrl"].endswith("/_history/2")
    assert data["entry"][1]["resource"]["comment"] == "Second version"
    assert data["entry"][0]["fullUrl"].endswith("/_history/3")
    assert data["entry"][0]["resource"]["comment"] == "Third version"

    bundle = Bundle(**data)
    assert isinstance(bundle, Bundle)

    response = api_client.request("GET", f"{healthcareservice_endpoint}/{str(id)}/_history/2")
    assert response.status_code == 200
    assert response.headers["etag"] == 'W/"2"'
    data = response.json()
    assert data["resourceType"] == "HealthcareService"
    assert data["comment"] == "Second version"


def generate_entity(id: UUID, service: HealthcareServiceService, comment: str | None = None) -> HealthcareService:
    """
    Generate a new entity and insert it into the database. If the entity already exists, update it by adding a new
    version with the same ID
    """
    dg = DataGenerator()
    entity = dg.generate_healthcare_service(id, comment)

    try:
        service.get_one(id)
        return service.update_one(id, entity)
    except ResourceNotFoundException:
        return service.add_one(entity, id=id)
