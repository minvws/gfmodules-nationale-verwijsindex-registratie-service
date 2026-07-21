import configparser
import os
from enum import Enum
from typing import Any, List

from pydantic import BaseModel, Field, field_validator

_PATH = "app.conf"
_CONFIG = None
_ENVIRONMENT_CONFIG_PATH_NAME = "FASTAPI_CONFIG_PATH"


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class ConfigApp(BaseModel):
    loglevel: LogLevel = Field(default=LogLevel.info)
    data_domains: List[str] = Field(default=[])
    org_registration_ura: str = Field(default="")
    org_registration_oin: str = Field(default="")
    source_id: str = Field(default="")

    @field_validator("data_domains", mode="before")
    @classmethod
    def split_values(cls, value: object) -> List[str]:
        if isinstance(value, str):
            value = "".join(value.split())
            value_list = [] if value == "" else value.split(",")
            return [data_domain for data_domain in value_list]

        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            return []

        return value


class ConfigScheduler(BaseModel):
    scheduled_delay: int = Field(default=5)
    automatic_background_update: bool = Field(default=True)


class ConfigMetadataApi(BaseModel):
    mock: bool = Field(default=False)
    endpoint: str = Field(default="")
    timeout: int = Field(default=30, gt=0)
    mtls_cert: str | None = Field(default=None)
    mtls_key: str | None = Field(default=None)
    verify_ca: str | bool = Field(default=True)


class ConfigPseudonymApi(BaseModel):
    mock: bool = Field(default=False)
    endpoint: str = Field(default="")
    timeout: int = Field(default=30, gt=0)
    mtls_cert: str | None = Field(default=None)
    mtls_key: str | None = Field(default=None)
    verify_ca: str | bool = Field(default=True)


class ConfigReferralApi(BaseModel):
    mock: bool = Field(default=False)
    endpoint: str = Field(default="")
    timeout: int = Field(default=30, gt=0)
    mtls_cert: str | None = Field(default=None)
    mtls_key: str | None = Field(default=None)
    verify_ca: str | bool = Field(default=True)
    nvi_oin: str = Field(default="")


class ConfigOauthApi(BaseModel):
    mock: bool = Field(default=False)
    nvi_endpoint: str = Field(default="")
    prs_endpoint: str = Field(default="")
    nvi_audience: str = Field(default="")
    prs_audience: str = Field(default="")
    timeout: int = Field(default=30, gt=0)
    mtls_cert: str | None = Field(default=None)
    mtls_key: str | None = Field(default=None)
    verify_ca: str | bool = Field(default=True)
    include_x5c: bool = Field(default=True)


class NviFhirSystems(BaseModel):
    extension_identifier: str = Field(default="http://fhir.nl/fhir/NamingSystem/ura")
    extension_url: str = Field(
        default="http://minvws.github.io/generiekefuncties-docs/StructureDefinition/nl-gf-localization-custodian"
    )
    subject_system: str = Field(default="http://minvws.github.io/generiekefuncties-docs/NamingSystem/nvi-identifier")
    source_system: str = Field(default="urn:ietf:rfc:3986")
    coding_system: str = Field(
        default="http://minvws.github.io/generiekefuncties-docs/CodeSystem/nl-gf-data-categories-cs"
    )


class ConfigUvicorn(BaseModel):
    swagger_enabled: bool = Field(default=False)
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8501, gt=0, lt=65535)
    reload: bool = Field(default=True)
    reload_delay: float = Field(default=1)
    reload_dirs: list[str] = Field(default=["app"])
    use_ssl: bool = Field(default=False)
    ssl_base_dir: str | None
    ssl_cert_file: str | None
    ssl_key_file: str | None


class Config(BaseModel):
    app: ConfigApp
    scheduler: ConfigScheduler
    metadata_api: ConfigMetadataApi
    uvicorn: ConfigUvicorn
    pseudonym_api: ConfigPseudonymApi
    referral_api: ConfigReferralApi
    oauth_api: ConfigOauthApi
    nvi_fhir_systems: NviFhirSystems
    overwrite_headers: dict[str, str] = Field(default_factory=dict)


def read_ini_file(path: str) -> Any:
    ini_data = configparser.ConfigParser()
    ini_data.read(path)

    ret = {}
    for section in ini_data.sections():
        ret[section] = dict(ini_data[section])

    return ret


def reset_config() -> None:
    global _CONFIG
    _CONFIG = None


def set_config(config: Config) -> None:
    global _CONFIG
    _CONFIG = config


def get_config(path: str | None = None) -> Config:
    global _CONFIG
    global _PATH

    if _CONFIG is not None:
        return _CONFIG

    if path is None:
        path = path or os.environ.get(_ENVIRONMENT_CONFIG_PATH_NAME) or _PATH

    # To be inline with other python code, we use INI-type files for configuration. Since this isn't
    # a standard format for pydantic, we need to do some manual parsing first.
    ini_data = read_ini_file(path)

    _CONFIG = Config(**ini_data)
    return _CONFIG
