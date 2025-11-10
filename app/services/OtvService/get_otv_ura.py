from app.config import ConfigOtvStubUra
from app.models.ura_number import UraNumber


def get_otv_ura(otv_stub_certificate: ConfigOtvStubUra) -> UraNumber:
    """Get the OTV URA number either from the certificate or from the override in config."""
    if otv_stub_certificate.otv_stub_ura_override is not None:
        try:
            ura_number = UraNumber(otv_stub_certificate.otv_stub_ura_override)
            return ura_number
        except Exception as e:
            raise ValueError("Invalid otv_stub_ura_override provided in config") from e
    try:
        with open(otv_stub_certificate.otv_stub_certificate_path, "r") as cert_data:  # type: ignore
            cert_ura = UraNumber.from_certificate(cert_data.read())
            if cert_ura is None:
                raise ValueError("Failed to read UraNumber from otv_stub_certificate_path")
            return cert_ura
    except Exception as e:
        raise ValueError("Could not set UraNumber from otv_stub_certificate_path") from e
