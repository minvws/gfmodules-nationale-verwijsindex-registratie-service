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
    provider_id: str
    data_domains: List[str] = Field(default=[])
    default_organization_type: str = Field(default="hospital")

    @field_validator("data_domains", mode="before")
    @classmethod
    def split_values(cls, value: object) -> object:
        if isinstance(value, str):
            value = "".join(value.split())
            return [] if value == "" else value.split(",")
        return value


class ConfigScheduler(BaseModel):
    scheduled_delay: int = Field(default=5)
    automatic_background_update: bool = Field(default=True)


class ConfigMetadataApi(BaseModel):
    mock: bool = Field(default=False)
    endpoint: str
    timeout: int = Field(default=30, gt=0)
    mtls_cert: str | None = Field(default=None)
    mtls_key: str | None = Field(default=None)
    mtls_ca: str | None = Field(default=None)


class ConfigPseudonymApi(BaseModel):
    mock: bool = Field(default=False)
    endpoint: str
    timeout: int = Field(default=30, gt=0)
    mtls_cert: str | None = Field(default=None)
    mtls_key: str | None = Field(default=None)
    mtls_ca: str | None = Field(default=None)


class ConfigReferralApi(BaseModel):
    mock: bool = Field(default=False)
    endpoint: str
    timeout: int = Field(default=30, gt=0)
    mtls_cert: str | None = Field(default=None)
    mtls_key: str | None = Field(default=None)
    mtls_ca: str | None = Field(default=None)


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
