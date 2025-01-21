from typing import Literal, Union

import pytest

from app.db.db import Database
from app.params.endpoint_query_params import EndpointQueryParams
from app.params.organization_query_params import OrganizationQueryParams
from app.services.entity_services.endpoint_service import EndpointService
from app.services.entity_services.organization_service import OrganizationService
from app.services.matching_care_service import MatchingCareService
from tests.utils import add_endpoint, add_organization, check_key_value


@pytest.mark.parametrize(
    "ura, active, name, parent_organization, include, rev_include",
    [
        (True, True, "Org A", False, None, None),
        (True, False, "Org B", True, "Organization.endpoint", None),
        (True, False, None, False, None, "Location:organization"),
        (
            True,
            True,
            "Org C",
            True,
            None,
            "OrganizationAffiliation:primary-organization",
        ),
        (
            True,
            True,
            "Org D",
            False,
            "Organization.endpoint",
            "OrganizationAffiliation:participating-organization",
        ),
        (
            True,
            False,
            "Org E",
            True,
            None,
            "OrganizationAffiliation:primary-organization",
        ),
        (True, False, "Org F", None, None, "Location:organization"),
        (
            True,
            True,
            None,
            False,
            None,
            "OrganizationAffiliation:primary-organization",
        ),
        (
            True,
            False,
            "Org G",
            False,
            None,
            "OrganizationAffiliation:participating-organization",
        ),
        (True, True, None, True, None, "Location:organization"),
        (True, None, "Org H", True, "Organization.endpoint", None),
        (
            True,
            False,
            "Org I",
            True,
            None,
            "OrganizationAffiliation:primary-organization",
        ),
        (True, True, "Org J", None, None, "Location:organization"),
        (
            True,
            None,
            "Org K",
            False,
            None,
            "OrganizationAffiliation:primary-organization",
        ),
        (True, True, None, True, None, None),
    ],
)
def test_find_correct_organizations(
    organization_service: OrganizationService,
    endpoint_service: EndpointService,
    matching_care_service: MatchingCareService,
    ura: bool,
    active: bool,
    name: str,
    parent_organization: bool,
    include: Literal["Organization.endpoint"] | None,
    rev_include: Union[
        Literal[
            "Location:organization",
            "OrganizationAffiliation:participating-organization",
            "OrganizationAffiliation:primary-organization",
        ]
    ],
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()

    expected_endpoint = add_endpoint(endpoint_service) if include else None
    part_of_id = add_organization(organization_service).fhir_id if parent_organization else None

    expected_org = add_organization(
        organization_service=organization_service,
        active=active,
        name=name,
        endpoint_id=expected_endpoint.fhir_id if include is not None else None,  # type: ignore
        part_of=part_of_id if parent_organization else None,
    )

    query_params = OrganizationQueryParams(
        active=active if active is not None else None,
        identifier=expected_org.ura_number if ura else None,
        name=name if name is not None else None,
        partOf=str(part_of_id) if parent_organization else None,
        _include=include if include is not None else None,
        # _revInclude=rev_include,
        endpoint=str(expected_endpoint.fhir_id) if include is not None else None,  # type: ignore
    )

    result = matching_care_service.find_organizations(query_params)

    assert result is not None
    assert check_key_value(result.dict(), "id", str(expected_org.fhir_id))
    if active is not None:
        assert check_key_value(result.dict(), "active", active)
    assert check_key_value(result.dict(), "value", expected_org.ura_number)
    if name is not None:
        assert check_key_value(result.dict(), "name", name)
    if include is not None:
        assert check_key_value(
            result.dict(),
            "reference",
            "Endpoint/" + str(expected_endpoint.fhir_id),  # type: ignore
        )


def test_find_correct_endpoints(
    organization_service: OrganizationService,
    endpoint_service: EndpointService,
    matching_care_service: MatchingCareService,
    setup_postgres_database: Database,
) -> None:
    setup_postgres_database.truncate_tables()
    expected_org = add_organization(organization_service)
    expected_endpoint = add_endpoint(endpoint_service, org_fhir_id=expected_org.fhir_id)

    endpoint_params = EndpointQueryParams(
        _id=expected_endpoint.fhir_id,
        organization=str(expected_org.fhir_id),
    )

    endpoints = matching_care_service.find_endpoints(endpoint_params)
    assert endpoints is not None
    assert check_key_value(endpoints.dict(), "reference", f"Organization/{expected_org.fhir_id}")
    assert check_key_value(endpoints.dict(), "id", expected_endpoint.fhir_id)
    assert check_key_value(endpoints.dict(), "address", expected_endpoint.data.get("address"))  # type: ignore
