from fhir.resources.R4B.reference import Reference

from app.services.parsers.reference import ReferenceParser


def test_get_reference_type_and_id_should_succeed() -> None:
    expected_type = "Patient"
    expected_id = "some-id"
    reference = Reference(reference=f"{expected_type}/{expected_id}")

    actual_type, actual_id = ReferenceParser.get_reference_type_and_id(reference)

    assert (actual_type, actual_id) == (expected_type, expected_id)


def test_get_reference_should_return_None_with_empty_reference() -> None:
    reference = Reference(type="Patient", id="some-id", reference="#reference")

    expected_type, expected_id = ReferenceParser.get_reference_type_and_id(reference)

    assert (expected_type, expected_id) == (None, None)
