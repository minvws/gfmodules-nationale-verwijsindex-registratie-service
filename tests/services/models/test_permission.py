from app.models.permission import (
    OtvStubDto,
    OtvStubPermissionRequest,
    OtvStubResourceDto,
    OtvStubSubjectDto,
    PermissionRequestModel,
)
from app.models.pseudonym import Pseudonym
from app.models.ura_number import UraNumber


def test_create_otv_stub_resource_dto() -> None:
    dto = OtvStubResourceDto(
        pseudonym="pseudonym_value",
        org_ura="org_ura_value",
        org_category="org_category_value",
    )
    assert dto.pseudonym == "pseudonym_value"
    assert dto.org_ura == "org_ura_value"
    assert dto.org_category == "org_category_value"


def test_otv_stub_subject_dto() -> None:
    dto = OtvStubSubjectDto(
        org_ura="org_ura_value",
    )
    assert dto.org_ura == "org_ura_value"


def test_create_otv_stub_dto() -> None:
    resource_dto = OtvStubResourceDto(
        pseudonym="pseudonym_value",
        org_ura="org_ura_value",
        org_category="org_category_value",
    )
    subject_dto = OtvStubSubjectDto(
        org_ura="org_ura_value",
    )
    dto = OtvStubDto(
        resource=resource_dto,
        subject=subject_dto,
    )
    assert dto.resource == resource_dto
    assert dto.subject == subject_dto


def test_create_otv_stub_permission_request() -> None:
    pseudonym = Pseudonym(pseudonym="pseudonym_value")
    ura_number = UraNumber("1234567")
    request = OtvStubPermissionRequest(
        reversible_pseudonym=pseudonym,
        client_ura_number=ura_number,
    )
    assert request.reversible_pseudonym == pseudonym
    assert request.client_ura_number == ura_number


def test_create_permission_request_model() -> None:
    request = PermissionRequestModel(
        encrypted_lmr_id="encrypted_id_value",
        client_ura_number="1234567",
    )
    assert request.encrypted_lmr_id == "encrypted_id_value"
    assert request.client_ura_number == UraNumber("1234567")


def test_permission_request_model_validator() -> None:
    request = PermissionRequestModel(
        encrypted_lmr_id="encrypted_id_value",
        client_ura_number=UraNumber("1234567"),
    )
    assert request.client_ura_number == UraNumber("1234567")
