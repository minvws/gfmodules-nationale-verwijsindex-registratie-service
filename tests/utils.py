# Helper function to check whether Bundle result contains the correct key and value
from typing import Any, Optional
from uuid import UUID

from faker import Faker
from fhir.resources.R4B.endpoint import Endpoint as FhirEndpoint

from app.data import EndpointStatus
from app.db.entities.endpoint.endpoint import Endpoint
from app.db.entities.location.location import Location
from app.db.entities.organization.organization import Organization
from app.db.entities.organization_affiliation.organization_affiliation import (
    OrganizationAffiliation,
)
from app.db.entities.practitioner.practitioner import Practitioner
from app.db.entities.practitioner_role.practitioner_role import PractitionerRole
from app.services.entity_services.endpoint_service import EndpointService
from app.services.entity_services.location_service import LocationService
from app.services.entity_services.organization_affiliation_service import (
    OrganizationAffiliationService,
)
from app.services.entity_services.organization_service import OrganizationService
from app.services.entity_services.practitioner import PractitionerService
from app.services.entity_services.practitioner_role_service import PractitionerRoleService
from seeds.generate_data import DataGenerator

fake = Faker("nl_nl")


def check_key_value(data: dict[Any, Any] | list[Any], key_to_check: Any, value_to_check: Any) -> bool:
    """
    Recursively checks if the specified key exists in the dictionary or list
    and if its value matches the specified value.

    Args:
        data: The dictionary or list to check.
        key_to_check: The key to look for.
        value_to_check: The value to check against.

    Returns:
        bool: True if the key is found with the specified value, otherwise False.
    """
    if isinstance(data, dict):
        return any(
            (str(key) == str(key_to_check) and str(value) == str(value_to_check))
            or (isinstance(value, (dict, list)) and check_key_value(value, key_to_check, value_to_check))
            for key, value in data.items()
        )
    if isinstance(data, list):
        return any(check_key_value(item, key_to_check, value_to_check) for item in data)


# Helper function to add an organization
def add_organization(
    organization_service: OrganizationService,
    active: Optional[bool] = None,
    ura_number: Optional[str] = None,
    name: Optional[str] = None,
    uuid: Optional[str] = None,
    endpoint_id: Optional[UUID] = None,
    part_of: Optional[UUID] = None,
) -> Organization:
    dg = DataGenerator()
    return organization_service.add_one(dg.generate_organization(ura_number, active, name, uuid, endpoint_id, part_of))


# Helper function to add an organization affiliation
def add_organization_affiliation(
    organization_affiliation_service: OrganizationAffiliationService,
    active: Optional[bool] = None,
    organization: Optional[UUID] = None,
    participation_organization: Optional[UUID] = None,
) -> OrganizationAffiliation:
    dg = DataGenerator()
    return organization_affiliation_service.add_one(
        dg.generate_organization_affiliation(active, organization, participation_organization)
    )


# Helper function to add a practitioner
def add_practitioner(
    practitioner_service: PractitionerService,
    active: Optional[bool] = None,
    qualifications: Optional[list[UUID]] = None,
) -> Practitioner:
    dg = DataGenerator()
    return practitioner_service.add_one(dg.generate_practitioner(active, qualifications))


# Helper function to add a practitioner role
def add_practitioner_role(
    practitioner_role_service: PractitionerRoleService,
    organization: Optional[UUID] = None,
) -> PractitionerRole:
    dg = DataGenerator()
    return practitioner_role_service.add_one(
        dg.generate_practitioner_role(
            id=fake.uuid4(),
            organization=organization,
        )
    )


# Helper function to add a location
def add_location(
    location_service: LocationService,
    organization: Optional[UUID] = None,
    part_of: Optional[UUID] = None,
) -> Location:
    dg = DataGenerator()
    return location_service.add_one(dg.generate_location(organization, part_of))


# Helper function to add an endpoint
def add_endpoint(
    endpoint_service: EndpointService,
    status: Optional[EndpointStatus] = None,
    uuid: Optional[UUID] = None,
    org_fhir_id: Optional[UUID] = None,
    name: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    complete_endpoint: FhirEndpoint | None = None,
) -> Endpoint:
    dg = DataGenerator()
    return (
        endpoint_service.add_one(
            dg.generate_endpoint(
                org_fhir_id=org_fhir_id,
                status=str(status),
                name=name,
                uuid_identifier=uuid,
                endpoint_url=endpoint_url,
            )
        )
        if complete_endpoint is None
        else endpoint_service.add_one(complete_endpoint)
    )
