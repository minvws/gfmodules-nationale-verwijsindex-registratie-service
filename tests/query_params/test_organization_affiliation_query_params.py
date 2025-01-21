from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.params.affiliation_query_params import OrganizationAffliliationQueryParams


@pytest.mark.parametrize(
    "expected_query_params",
    [
        {
            "id": uuid4(),
            "active": True,
            "participating_organization": uuid4(),
            "primary_organization": uuid4(),
        },
        {
            "active": False,
            "include": "OrganizationAffiliation.endpoint",
            "role": "some role",
        },
    ],
)
def test_query_params_creation_should_succeed_when_correct_values_are_passed(
    expected_query_params: dict[str, Any],
) -> None:
    model = OrganizationAffliliationQueryParams(**expected_query_params)

    actual_query_params = model.model_dump(exclude_none=True, by_alias=False)
    assert expected_query_params == actual_query_params


@pytest.mark.parametrize(
    "incorrect_params",
    [
        {"id": uuid4(), "include": "OrganizationAffiliation.wrong-join"},
        {
            "active": True,
            "primary_organization": uuid4(),
            "participating_organization": uuid4(),
            "include": "IncorrectResource.endpoint",
        },
    ],
)
def test_incorrect_values_in_query_params_should_raise_value_error_when_incorrect_litrals_are_passed(
    incorrect_params: dict[str, Any],
) -> None:
    with pytest.raises(ValidationError, match=r".* validation error .*"):
        OrganizationAffliliationQueryParams.model_validate(incorrect_params)
