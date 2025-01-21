from app.config import (
    Config,
    ConfigApp,
    ConfigDatabase,
    ConfigStats,
    ConfigTelemetry,
    ConfigUvicorn,
    LogLevel,
)
from app.db.db import Database


def get_test_config(database: ConfigDatabase | None = None) -> Config:
    if not database:
        database = ConfigDatabase(
            dsn="sqlite:///:memory:",
            create_tables=True,
            retry_backoff=[0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 4.8, 6.4, 10.0],
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=False,
            pool_recycle=1,
        )

    return Config(
        app=ConfigApp(
            loglevel=LogLevel.error,
            override_authentication_ura=None,
        ),
        database=database,
        uvicorn=ConfigUvicorn(
            swagger_enabled=False,
            docs_url="/docs",
            redoc_url="/redoc",
            host="0.0.0.0",
            port=8503,
            reload=True,
            use_ssl=False,
            ssl_base_dir=None,
            ssl_cert_file=None,
            ssl_key_file=None,
        ),
        telemetry=ConfigTelemetry(
            enabled=False,
            endpoint=None,
            service_name=None,
            tracer_name=None,
        ),
        stats=ConfigStats(enabled=False, host=None, port=None, module_name=None),
    )


def get_test_config_with_postgres_db_connection() -> Config:
    return get_test_config(database=get_database_config_postgres_db())


def get_database_config_postgres_db() -> ConfigDatabase:
    return ConfigDatabase(
        dsn=get_postgres_db_connection_dsn(),
        create_tables=False,
        retry_backoff=[0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 4.8, 6.4, 10.0],
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=False,
        pool_recycle=1,
    )


def get_postgres_db_connection_dsn() -> str:
    return "postgresql+psycopg://postgres:postgres@addressing_db:5432/testing"


def get_postgres_database() -> Database:
    return Database(config=get_database_config_postgres_db())
