import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import (
    Config,
    ConfigApp,
    ConfigMetadataApi,
    ConfigOtvStubApi,
    ConfigOtvStubUra,
    ConfigPseudonymApi,
    ConfigReferralApi,
    ConfigScheduler,
    ConfigUvicorn,
    LogLevel, ConfigLmr,
)


def get_test_config() -> Config:
    return Config(
        app=ConfigApp(loglevel=LogLevel.error, provider_id="00000001"),
        pseudonym_api=ConfigPseudonymApi(endpoint="http://example.com", mtls_key=""),
        referral_api=ConfigReferralApi(endpoint="http://example.com"),
        uvicorn=ConfigUvicorn(
            swagger_enabled=False,
            docs_url="/docs",
            redoc_url="/redoc",
            host="0.0.0.0",
            port=8515,
            reload=True,
            use_ssl=False,
            ssl_base_dir=None,
            ssl_cert_file=None,
            ssl_key_file=None,
        ),
        metadata_api=ConfigMetadataApi(
            mock=True,
            endpoint="http://example.com",
            timeout=30,
            mtls_cert=None,
            mtls_key=None,
            mtls_ca=None,
        ),
        scheduler=ConfigScheduler(scheduled_delay=5),
        otv_stub_api=ConfigOtvStubApi(
            mock=True,
            endpoint="http://example.com",
            timeout=30,
            mtls_cert=None,
            mtls_key=None,
            mtls_ca=None,
        ),
        otv_stub_certificate=ConfigOtvStubUra(
            otv_stub_certificate_path=None,
            otv_stub_ura_override="12345678",
        ),
        lmr=ConfigLmr(encryption_key=base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=128)).decode())
    )
