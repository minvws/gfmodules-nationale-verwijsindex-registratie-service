import pytest
from pytest_mock import MockerFixture

from app.config import ConfigPseudonymApi
from app.models.ura_number import UraNumber
from app.services.registration_service import PrsRegistrationService, PseudonymError


def test_register_nvi_rs_at_prs_success(
    prs_registration_service: PrsRegistrationService,
    mocker: MockerFixture,
) -> None:
    post_mock = mocker.patch("requests.post")
    post_mock.return_value.status_code = 201

    prs_registration_service.register_nvi_rs_at_prs()

    assert post_mock.call_count == 2
    org_call = post_mock.call_args_list[0]
    cert_call = post_mock.call_args_list[1]

    assert org_call[1]["url"].endswith("/orgs")
    assert cert_call[1]["url"].endswith("/register/certificate")

    assert org_call[1]["json"]["ura"] == "12345678"
    assert org_call[1]["json"]["name"] == "nationale-verwijsindex-registratie-service"
    assert org_call[1]["json"]["max_key_usage"] == "rp"

    assert cert_call[1]["json"]["scope"] == ["nationale-verwijsindex-registratie-service"]


def test_register_nvi_rs_at_prs_org_already_registered(
    prs_registration_service: PrsRegistrationService,
    mocker: MockerFixture,
) -> None:
    post_mock = mocker.patch("requests.post")
    logging_mock = mocker.patch("app.services.registration_service.logger")
    post_mock.side_effect = [
        mocker.Mock(status_code=409),  # Organization already registered
        mocker.Mock(status_code=201),  # Certificate registration success
    ]

    prs_registration_service.register_nvi_rs_at_prs()

    assert post_mock.call_count == 2
    logging_mock.info.assert_any_call("Organization already registered at PRS")


def test_register_nvi_rs_at_prs_cert_already_registered(
    prs_registration_service: PrsRegistrationService,
    mocker: MockerFixture,
) -> None:
    post_mock = mocker.patch("requests.post")
    logging_mock = mocker.patch("app.services.registration_service.logger")
    post_mock.side_effect = [
        mocker.Mock(status_code=201),  # Organization registration success
        mocker.Mock(status_code=409),  # Certificate already registered
    ]

    prs_registration_service.register_nvi_rs_at_prs()

    assert post_mock.call_count == 2
    logging_mock.info.assert_any_call("Certificate already registered at PRS")


def test_register_nvi_rs_at_prs_failure(
    prs_registration_service: PrsRegistrationService,
    mocker: MockerFixture,
) -> None:
    post_mock = mocker.patch("requests.post")
    post_mock.side_effect = Exception("Network error")

    with pytest.raises(Exception) as excinfo:
        prs_registration_service.register_nvi_rs_at_prs()

    assert "Failed to register nvi_rs at PRS" in str(excinfo.value)
    assert post_mock.call_count == 1
    assert isinstance(excinfo.value, PseudonymError)


def test_register_nvi_rs_at_prs_mock_mode(
    config_pseudonym_api: ConfigPseudonymApi,
    ura_number: UraNumber,
    mocker: MockerFixture,
) -> None:
    config_pseudonym_api.mock = True
    prs_registration_service = PrsRegistrationService(
        conf=config_pseudonym_api,
        ura_number=ura_number,
    )

    post_mock = mocker.patch("requests.post")
    logging_mock = mocker.patch("app.services.registration_service.logger")

    prs_registration_service.register_nvi_rs_at_prs()

    post_mock.assert_not_called()
    logging_mock.info.assert_any_call("Mock mode enabled, skipping registration at PRS")
