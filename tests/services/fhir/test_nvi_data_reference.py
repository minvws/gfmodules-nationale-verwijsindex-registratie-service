import pytest

from app.models.data_domain import DataDomain
from app.models.pseudonym import OprfPseudonymJWE
from app.models.referrals import CreateReferralRequest
from app.models.ura_number import UraNumber
from app.services.fhir.nvi_data_reference import NviDataReferenceMapper


@pytest.fixture
def mapper() -> NviDataReferenceMapper:
    return NviDataReferenceMapper(
        pseudonym_system="http://example.com/some-pseudonym-system",
        source_system="urn:oid:2.16.528.1.1007.3.3",
        organization_type_system="http://example.com/some-org-type-system",
        care_context_system="http://example.com/some-care-context-system",
    )


@pytest.fixture
def sample_request() -> CreateReferralRequest:
    return CreateReferralRequest(
        oprf_jwe=OprfPseudonymJWE(jwe="fake_jwe"),
        blind_factor="base64-encoded-oprf-key",
        ura_number=UraNumber("90000001"),
        organization_type="laboratorium",
        data_domain=DataDomain("LaboratoryTestResult"),
    )


def test_to_fhir_structure(mapper: NviDataReferenceMapper, sample_request: CreateReferralRequest) -> None:
    result = mapper.to_fhir(sample_request)

    expected = {
        "resourceType": "NVIDataReference",
        "subject": {
            "system": "http://example.com/some-pseudonym-system",
            "value": "fake_jwe",
        },
        "source": {
            "system": "urn:oid:2.16.528.1.1007.3.3",
            "value": "90000001",
        },
        "sourceType": {
            "coding": [
                {
                    "system": "http://example.com/some-org-type-system",
                    "code": "laboratorium",
                    "display": "Laboratorium",
                }
            ]
        },
        "careContext": {
            "coding": [
                {
                    "system": "http://example.com/some-care-context-system",
                    "code": "LaboratoryTestResult",
                }
            ]
        },
        "oprfKey": "base64-encoded-oprf-key",
    }

    assert result == expected


def test_custom_systems_configuration(sample_request: CreateReferralRequest) -> None:
    custom_mapper = NviDataReferenceMapper(
        pseudonym_system="http://custom.example/pseudonym",
        source_system="urn:custom:source",
        organization_type_system="http://custom.example/org-types",
        care_context_system="http://custom.example/care-context",
    )

    result = custom_mapper.to_fhir(sample_request)

    assert result["subject"]["system"] == "http://custom.example/pseudonym"
    assert result["source"]["system"] == "urn:custom:source"
    assert result["sourceType"]["coding"][0]["system"] == "http://custom.example/org-types"
    assert result["careContext"]["coding"][0]["system"] == "http://custom.example/care-context"
