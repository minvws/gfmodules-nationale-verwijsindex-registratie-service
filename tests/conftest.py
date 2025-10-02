from datetime import datetime
from typing import Any, Dict

import pytest
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.imagingstudy import ImagingStudy
from fhir.resources.R4B.patient import Patient

from app.models.metadata.params import MetadataResourceParams
from app.models.pseudonym import Pseudonym
from app.models.referrals import CreateReferralDTO, Referral, ReferralQueryDTO
from app.models.update_scheme import BsnUpdateScheme
from app.services.api.fhir import FhirHttpService
from app.services.domain_map_service import DomainsMapService
from app.services.metadata import BSN_SYSTEM, MetadataService
from app.services.nvi import NviService
from app.services.pseudonym import PseudonymService
from app.services.synchronizer import Synchronizer


@pytest.fixture
def mock_url() -> str:
    return "http://example.org/fhir/"


@pytest.fixture
def mock_ura_number() -> str:
    return "12345678"


@pytest.fixture
def domains_map_service() -> DomainsMapService:
    return DomainsMapService()


@pytest.fixture
def fhir_http_service(mock_url: str) -> FhirHttpService:
    return FhirHttpService(endpoint=mock_url, timeout=1, mtls_ca=None, mtls_cert=None, mtls_key=None)


@pytest.fixture
def pseudonym_service(mock_url: str, mock_ura_number: str) -> PseudonymService:
    return PseudonymService(
        provider_id=mock_ura_number,
        endpoint=mock_url,
        timeout=1,
        mtls_cert=None,
        mtls_key=None,
        mtls_ca=None,
    )


@pytest.fixture
def nvi_service(mock_url: str) -> NviService:
    return NviService(endpoint=mock_url, timeout=1, mtls_cert=None, mtls_key=None, mtls_ca=None)


@pytest.fixture
def metadata_service(mock_url: str) -> MetadataService:
    return MetadataService(endpoint=mock_url, timeout=1, mtls_cert=None, mtls_key=None, mtls_ca=None)


@pytest.fixture
def synchronizer(
    domains_map_service: DomainsMapService,
    pseudonym_service: PseudonymService,
    nvi_service: NviService,
    metadata_service: MetadataService,
    mock_ura_number: str,
) -> Synchronizer:
    return Synchronizer(
        nvi_api=nvi_service,
        pseudonym_api=pseudonym_service,
        metadata_api=metadata_service,
        domains_map_service=domains_map_service,
        ura_number=mock_ura_number,
    )


@pytest.fixture
def referral_query() -> ReferralQueryDTO:
    return ReferralQueryDTO(pseudonym="some_pseudonym", data_domain="some_domain", ura_number="1234566789")


@pytest.fixture
def create_referral_dto(referral_query: ReferralQueryDTO) -> CreateReferralDTO:
    return CreateReferralDTO(**referral_query.model_dump(), requesting_uzi_number="some_uzi_number")


@pytest.fixture
def mock_bsn_number() -> str:
    return "200060429"


@pytest.fixture
def datetime_past() -> str:
    return datetime(2022, 12, 10, 12, 0, 0, 0).isoformat()


@pytest.fixture
def datetime_now() -> str:
    return datetime(2025, 12, 10, 12, 0, 0, 0).isoformat()


@pytest.fixture
def mock_pseudonym() -> Pseudonym:
    return Pseudonym(pseudonym="some_pseudonym")


@pytest.fixture
def mock_referral(mock_ura_number: str, mock_pseudonym: Pseudonym) -> Referral:
    return Referral(
        pseudonym=mock_pseudonym.pseudonym,
        data_domain="beeldbank",
        ura_number=mock_ura_number,
    )


@pytest.fixture
def bsn_update_scheme(mock_bsn_number: str, mock_referral: Referral) -> BsnUpdateScheme:
    return BsnUpdateScheme(bsn=mock_bsn_number, referral=mock_referral)


@pytest.fixture
def mock_imaging_study(datetime_past: str) -> Dict[str, Any]:
    return {
        "resourceType": "ImagingStudy",
        "id": "example-imagingstudy",
        "meta": {"lastUpdated": datetime_past},
        "identifier": [{"system": "http://example.com", "value": "some-identifier"}],
        "status": "available",
        "subject": {
            "reference": "Patient/example-patient",
            "display": "Example Patient",
        },
        "started": "2025-09-29T10:00:00Z",
        "numberOfSeries": 1,
        "numberOfInstances": 1,
        "series": [
            {
                "uid": "some-uid",
                "number": 1,
                "modality": {
                    "system": "http://dicom.nema.org/resources/ontology/DCM",
                    "code": "CT",
                    "display": "CT",
                },
                "description": "Example CT series",
                "numberOfInstances": 1,
                "instance": [
                    {
                        "uid": "some-uid",
                        "sopClass": {
                            "system": "urn:ietf:rfc:3986",
                            "code": "1.2.840.10008.5.1.4.1.1.2",
                            "display": "CT Image Storage (example)",
                        },
                        "number": 1,
                        "title": "Example instance",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def imaging_study(mock_imaging_study: Dict[str, Any]) -> ImagingStudy:
    return ImagingStudy.model_validate(mock_imaging_study)


@pytest.fixture
def mock_patient(mock_bsn_number: str, datetime_now: str) -> Dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "example-patient",
        "meta": {"lastUpdated": datetime_now},
        "identifier": [{"system": BSN_SYSTEM, "value": mock_bsn_number}],
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "gender": "female",
        "birthDate": "1990-02-17",
    }


@pytest.fixture
def patient(mock_patient: Dict[str, Any]) -> Patient:
    return Patient.model_validate(mock_patient)


@pytest.fixture
def mock_patient_without_bsn_system(mock_bsn_number: str, datetime_past: str) -> Dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "example-patient",
        "meta": {"lastUpdated": datetime_past},
        "identifier": [{"system": "SOME-SYSTEM-NOT-BSN-SYSTEM", "value": mock_bsn_number}],
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "gender": "female",
        "birthDate": "1990-02-17",
    }


@pytest.fixture
def mock_bundle(mock_patient: Dict[str, Any], mock_imaging_study: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [{"relation": "self", "url": "http://example.org"}],
        "entry": [
            {
                "resource": mock_patient,
            },
            {"resource": mock_imaging_study},
        ],
    }


@pytest.fixture
def regular_bundle(mock_bundle: Dict[str, Any]) -> Bundle:
    return Bundle.model_validate(mock_bundle)


@pytest.fixture
def mock_bundle_without_bsn_system(
    mock_imaging_study: Dict[str, Any], mock_patient_without_bsn_system: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [{"relation": "self", "url": "http://example.org"}],
        "entry": [
            {"resource": mock_imaging_study},
            {"resource": mock_patient_without_bsn_system},
        ],
    }


@pytest.fixture
def bundle_without_bsn_system(
    mock_bundle_without_bsn_system: Dict[str, Any],
) -> Bundle:
    return Bundle.model_validate(mock_bundle_without_bsn_system)


@pytest.fixture
def mock_bundle_without_patient(mock_imaging_study: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [{"relation": "self", "url": "http://example.org"}],
        "entry": [{"resource": mock_imaging_study}],
    }


@pytest.fixture
def bundle_without_patient(mock_bundle_without_patient: Dict[str, Any]) -> Bundle:
    return Bundle.model_validate(mock_bundle_without_patient)


@pytest.fixture
def query_param() -> Dict[str, Any]:
    return MetadataResourceParams(_include="ImagingStudy:subject", _lastUpdated=datetime.now().isoformat()).model_dump(
        by_alias=True
    )


@pytest.fixture
def query_params_without_last_update() -> Dict[str, Any]:
    return MetadataResourceParams(_include="ImagingStudy:subject").model_dump(by_alias=True, exclude_none=True)


@pytest.fixture()
def fhir_error() -> Dict[str, Any]:
    return {
        "resourceType": "OperationOutcome",
        "issue": [{"severity": "error", "code": "some_error", "diagnostics": "some_error"}],
    }
