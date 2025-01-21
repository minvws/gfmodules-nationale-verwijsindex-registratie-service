from contextlib import contextmanager
from typing import Any, Generator, Type
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.params.organization_query_params import OrganizationQueryParams


@contextmanager
def not_raise(validation_error: Type[Exception]) -> Generator[None, Any, Any]:
    try:
        yield
    except validation_error as e:
        pytest.fail("function did raise {0}".format(e))


@pytest.mark.parametrize(
    "expected_params",
    [
        {
            "id": uuid4(),
            "active": True,
            "ura_number": "some identifier",
            "parent_organization_id": "abc",
            "name": "Just a regular query parameter",
        },
        {
            "id": uuid4(),
            "active": True,
            "ura_number": "some identifier",
            "name": "with only include parameter",
            "include": "Organization.endpoint",
        },
        {"name": "with only revInclude", "rev_include": "Location:organization"},
        {
            "name": "combination of include and revInclude",
            "include": "Organization.endpoint",
            "rev_include": "OrganizationAffiliation:participating-organization",
        },
        {
            "name": "with a variation of revInclude",
            "include": "Organization.endpoint",
            "rev_include": "OrganizationAffiliation:primary-organization",
        },
    ],
)
def test_correct_query_params_should_succeed(expected_params: dict[str, Any]) -> None:
    actual_params = (OrganizationQueryParams(**expected_params)).model_dump(exclude_none=True)
    assert expected_params == actual_params


@pytest.mark.parametrize(
    "alias_params",
    [
        {
            "_id": uuid4(),
            "identifier": "1234567",
            "_revInclude": "OrganizationAffiliation:primary-organization",
            "_include": "Organization.endpoint",
        },
    ],
)
def test_using_alias_as_params_should_succeed(
    alias_params: dict[str, Any],
) -> None:
    with not_raise(ValidationError):
        OrganizationQueryParams.model_validate(alias_params)


@pytest.mark.parametrize(
    "incorrect_organization_params",
    [
        {"id": uuid4(), "include": "Organization.incorrectJoin"},
        {"id": uuid4(), "include": "IncorrectResource:endpoint"},
        {"id": uuid4(), "rev_include": "Location:incorrectJoin"},
        {"id": uuid4(), "rev_include": "IncorrectResource:primary-organization"},
        {"id": uuid4(), "rev_include": "IncorrectResource:participating-organization"},
        {"id": uuid4(), "rev_include": "OrganizationAffiliation:incorrect-join"},
        {
            "id": uuid4(),
            "name": "use dot instead of column",
            "_revInclude": "Location.organization",
        },
    ],
)
def test_incorrect_query_params_should_raise_value_error(
    incorrect_organization_params: dict[str, Any],
) -> None:
    with pytest.raises(ValueError):
        OrganizationQueryParams.model_validate(incorrect_organization_params)


@pytest.mark.parametrize(
    "incorrect_organization_params",
    [
        {"name": "Incorrect type", "id": 12345},
        {"name": "another incorrect type", "updated_at": ["some wrong data"]},
    ],
)
def test_incorrect_param_should_raise_validation_error(
    incorrect_organization_params: dict[str, Any],
) -> None:
    with pytest.raises(ValidationError):
        OrganizationQueryParams.model_validate(incorrect_organization_params)
