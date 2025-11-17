from app.config import ConfigOtvStubApi
from app.services.OtvService.interface import OtvService
from app.services.OtvService.mock import OtvMockService
from app.services.OtvService.otv_stub_service import OtvStubService


def create_otv_service(config: ConfigOtvStubApi) -> OtvService:
    if config.mock:
        return OtvMockService()
    if config.mtls_cert is None:
        raise ValueError("OTV stub mTLS certificate must be provided if not using mock.")

    return OtvStubService(
        endpoint=config.endpoint,
        timeout=config.timeout,
        mtls_cert=config.mtls_cert,
        mtls_key=config.mtls_key,
        mtls_ca=config.mtls_ca,
    )
