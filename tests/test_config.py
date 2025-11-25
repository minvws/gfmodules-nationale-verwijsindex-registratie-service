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
    LogLevel,
)


def get_test_config() -> Config:
    return Config(
        app=ConfigApp(loglevel=LogLevel.error, provider_id="00000001"),
        pseudonym_api=ConfigPseudonymApi(mock=True, endpoint="http://example.com", mtls_key=""),
        referral_api=ConfigReferralApi(mock=True, endpoint="http://example.com"),
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
        scheduler=ConfigScheduler(scheduled_delay=5, automatic_background_update=False),
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
    )
