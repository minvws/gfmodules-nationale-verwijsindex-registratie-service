from fhir.resources.R4B.patient import Patient

from app.services.parsers.patient import PatientParser


def test_get_patient_identifier_should_succeed(patient: Patient) -> None:
    assert patient.identifier  # happy typechecker
    expected = patient.identifier

    actual = PatientParser.get_identifiers([patient])

    assert expected == actual
