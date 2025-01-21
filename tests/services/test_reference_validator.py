from unittest.mock import MagicMock, Mock

import pytest
from fhir.resources.R4B.reference import Reference

from app.db.entities.healthcare_service.healthcare_service import HealthcareService
from app.db.session import DbSession
from app.exceptions.service_exceptions import ResourceNotFoundException
from app.services.reference_validator import ReferenceValidator


@pytest.fixture
def validator() -> ReferenceValidator:
    return ReferenceValidator()


@pytest.fixture
def session() -> Mock:
    return Mock(spec=DbSession)


def test_validate_reference_healthcare_service_valid(validator: ReferenceValidator, session: Mock) -> None:
    session.execute.return_value.first.return_value = HealthcareService(fhir_id="6b74c461-b19c-4860-b819-708997bb6b86")

    data = Reference.construct(reference="HealthcareService/6b74c461-b19c-4860-b819-708997bb6b86")
    validator.validate_reference(session, data, "HealthcareService")

    session.execute.assert_called_once()


def test_validate_reference_organization_affiliation_invalid(validator: ReferenceValidator, session: Mock) -> None:
    session.execute.return_value.first.return_value = None

    data = Reference.construct(reference="OrganizationAffiliation/c4f768a6-9190-4555-8c7d-ea577671515f")
    with pytest.raises(ResourceNotFoundException):
        validator.validate_reference(session, data, match_on="OrganizationAffiliation")
    session.execute.assert_called_once()


def test_validate_reference_invalid_reference_type(validator: ReferenceValidator, session: Mock) -> None:
    data = Reference.construct(reference="InvalidType/6b74c461-b19c-4860-b819-708997bb6b86")
    with pytest.raises(ValueError):
        validator.validate_reference(session, data, match_on="This_wont_match")


def test_validate_list_of_same_typed_references(validator: ReferenceValidator, session: Mock) -> None:
    session.execute.side_effect = [
        MagicMock(first=Mock(return_value=HealthcareService(fhir_id="6b74c461-b19c-4860-b819-708997bb6b86"))),
        MagicMock(first=Mock(return_value=HealthcareService(fhir_id="c4f768a6-9190-4555-8c7d-ea577671515f"))),
    ]

    data = [
        Reference.construct(reference="HealthcareService/6b74c461-b19c-4860-b819-708997bb6b86"),
        Reference.construct(reference="HealthcareService/c4f768a6-9190-4555-8c7d-ea577671515f"),
    ]

    validator.validate_list(session, data, match_on="HealthcareService")
    assert session.execute.call_count == 2


def test_validate_list_with_missing_reference(validator: ReferenceValidator, session: Mock) -> None:
    session.execute.side_effect = [
        MagicMock(first=Mock(return_value=HealthcareService(fhir_id="6b74c461-b19c-4860-b819-708997bb6b86"))),
        MagicMock(first=Mock(return_value=None)),
    ]

    data = [
        Reference.construct(reference="HealthcareService/6b74c461-b19c-4860-b819-708997bb6b86"),
        Reference.construct(reference="HealthcareService/c4f768a6-9190-4555-8c7d-ea577671515f"),
    ]

    with pytest.raises(ResourceNotFoundException):
        validator.validate_list(session, data, match_on="HealthcareService")


def test_validate_list_mixed_references_only_allow_single_type(validator: ReferenceValidator, session: Mock) -> None:
    session.execute.side_effect = [
        MagicMock(first=Mock(return_value=HealthcareService(fhir_id="6b74c461-b19c-4860-b819-708997bb6b86"))),
    ]

    data = [
        Reference.construct(reference="HealthcareService/6b74c461-b19c-4860-b819-708997bb6b86"),
        Reference.construct(reference="OrganizationAffiliation/c4f768a6-9190-4555-8c7d-ea577671515f"),
    ]

    with pytest.raises(ValueError):
        validator.validate_list(session, data, "HealthcareService")
