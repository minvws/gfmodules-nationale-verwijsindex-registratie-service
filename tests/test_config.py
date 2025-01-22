from app.config import (
    Config,
    ConfigApp,
    ConfigUvicorn,
    LogLevel,
)


def get_test_config() -> Config:
    return Config(
        app=ConfigApp(loglevel=LogLevel.error, provider_id="00000001", ura_number="00000012"),
        uvicorn=ConfigUvicorn(
            swagger_enabled=False,
            docs_url="/docs",
            redoc_url="/redoc",
            host="0.0.0.0",
            port=8510,
            reload=True,
            use_ssl=False,
            ssl_base_dir=None,
            ssl_cert_file=None,
            ssl_key_file=None,
        ),
    )
