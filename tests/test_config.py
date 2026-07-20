from app.config import (
    Config,
    ConfigApp,
    ConfigMetadataApi,
    ConfigPseudonymApi,
    ConfigReferralApi,
    ConfigOauthApi,
    ConfigScheduler,
    ConfigUvicorn,
    LogLevel,
    NviFhirSystems,
)


def get_test_config() -> Config:
    return Config(
        app=ConfigApp(
            loglevel=LogLevel.error,
        ),
        pseudonym_api=ConfigPseudonymApi(endpoint="http://example.com", mtls_key=""),
        referral_api=ConfigReferralApi(
            endpoint="http://example.com",
            nvi_oin="000000124",
        ),
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
        oauth_api=ConfigOauthApi(
            nvi_endpoint="http://example.com/oauth/token",
            prs_endpoint="http://example.com/oauth/token",
            timeout=30,
        ),
        metadata_api=ConfigMetadataApi(
            mock=True,
            endpoint="http://example.com",
            timeout=30,
            mtls_cert=None,
            mtls_key=None,
            verify_ca=True,
        ),
        scheduler=ConfigScheduler(scheduled_delay=5),
        nvi_fhir_systems=NviFhirSystems(),
    )
