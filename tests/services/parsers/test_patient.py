from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.patient import Patient

from app.data import BSN_SYSTEM
from app.services.parsers.patient import PatientParser


def test_get_patient_identifier_should_succeed(patient: Patient) -> None:
    assert patient.identifier  # happy typechecker
    expected = patient.identifier

    actual = PatientParser.get_identifiers([patient])

    assert expected == actual


def test_map_identifiers_to_bsn_should_succeed_and_return_ones_with_bsn() -> None:
    fake_bsn = "999990007"
    identifier_with_bsn_system = Identifier(system=BSN_SYSTEM, value=fake_bsn)
    identifier_without_bsn_system = Identifier(system="some-system", value="some-value")
    identifiers = [identifier_with_bsn_system, identifier_without_bsn_system]
    expected = [fake_bsn]

    actual = PatientParser.map_identifiers_to_bsn(identifiers)

    assert expected == actual
