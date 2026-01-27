from app.models.ura_number import UraNumber
from app.services.oauth.jwt_builder import JWTBuilder
from uzireader.uziserver import UziServer


def is_uzi_cert(cert_path: str) -> bool:
    with open(cert_path, "r", encoding="utf-8") as f:
        cert_pem = f.read()
    try:
        UziServer(verify="SUCCESS", cert=cert_pem)
        return True
    except Exception:
        return False


def initialize_jwt_builder(
    endpoint: str,
    ura_number: UraNumber,
    mtls_cert: str,
    uzi_cert_path: str | None,
    uzi_key_path: str | None,
    include_x5c: bool = True,
) -> JWTBuilder | None:
    if not is_uzi_cert(mtls_cert):
        if uzi_cert_path is None or uzi_key_path is None:
            raise ValueError("UZI cert/key paths not provided")
        return JWTBuilder(
            endpoint=endpoint,
            mtls_cert=mtls_cert,
            ura_number=ura_number,
            jwt_signing_cert=uzi_cert_path,
            jwt_signing_key=uzi_key_path,
            include_x5c=include_x5c,
        )
    else:
        return None
