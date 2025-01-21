import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fhir.resources.R4B.bundle import Bundle

from app.db.db import Database
from app.services.entity_services.endpoint_service import EndpointService
from seeds.generate_data import DataGenerator
from tests.utils import add_endpoint, check_key_value


@pytest.mark.parametrize(
    "url_suffix, expected_type",
    [
        ("/{id}", None),
        ("/_search", "searchset"),
        ("/_search/{id}", "searchset"),
    ],
)
def test_endpoint_routes(
    api_client: TestClient,
    endpoint_endpoint: str,
    endpoint_service: EndpointService,
    url_suffix: str,
    expected_type: str | None,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    expected = add_endpoint(endpoint_service)
    endpoint = endpoint_endpoint + url_suffix.format(id=expected.fhir_id)
    response = api_client.get(endpoint)
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
    endpoint_endpoint: str,
    endpoint_service: EndpointService,
) -> None:
    expected = add_endpoint(endpoint_service)
    response = api_client.request("DELETE", f"{endpoint_endpoint}/{expected.fhir_id}")
    assert response.status_code == 200


def test_update_endpoint(
    api_client: TestClient,
    endpoint_endpoint: str,
    endpoint_service: EndpointService,
) -> None:
    old = add_endpoint(endpoint_service)
    dg = DataGenerator()
    new_endpoint = dg.generate_endpoint()
    new_endpoint.id = str(old.fhir_id)  # type: ignore
    response = api_client.put(
        f"{endpoint_endpoint}/{old.fhir_id}",
        json=dict(jsonable_encoder(new_endpoint.dict())),
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["id"] == old.fhir_id.__str__()


def test_history_endpoint(
    api_client: TestClient,
    endpoint_endpoint: str,
    endpoint_service: EndpointService,
) -> None:
    endpoint = add_endpoint(endpoint_service)
    response = api_client.request("GET", f"{endpoint_endpoint}/{endpoint.fhir_id}/_history")
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "history"
    assert data["entry"][0]["resource"] == endpoint.data

    bundle = Bundle(**data)
    assert isinstance(bundle, Bundle)

    endpoint_2 = add_endpoint(endpoint_service)
    response = api_client.request(
        "GET",
        f"{endpoint_endpoint}/_history",
        params={"_since": endpoint_2.data.get("meta").get("lastUpdated")},  # type: ignore
    )
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 1  # Only endpoint_2 as it was created later than endpoint 1
    assert bundle.entry[0].resource.id == endpoint_2.fhir_id.__str__()  # type: ignore

    response = api_client.request(
        "GET",
        f"{endpoint_endpoint}/_history",  # Since creation of 1st endpoint
        params={"_since": endpoint.data.get("meta").get("lastUpdated")},
    )  # type: ignore
    assert response.status_code == 200
    bundle = Bundle(**response.json())
    assert isinstance(bundle, Bundle)
    assert bundle.type == "history"
    assert bundle.total == 2  # Both, because since is time of creation of first endpoint
    assert bundle.entry[0].resource.id == endpoint_2.fhir_id.__str__()  # type: ignore
    assert bundle.entry[1].resource.id == endpoint.fhir_id.__str__()  # type: ignore


def test_endpoint_version(
    api_client: TestClient,
    endpoint_endpoint: str,
    endpoint_service: EndpointService,
) -> None:
    endpoint = add_endpoint(endpoint_service)
    response = api_client.request("GET", f"{endpoint_endpoint}/{endpoint.fhir_id}/_history/{endpoint.version}")
    assert response.status_code == 200
    data = response.json()
    assert endpoint.data == data
    assert data["meta"]["versionId"] == endpoint.version
