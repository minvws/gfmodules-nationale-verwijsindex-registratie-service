from typing import Any, Dict
from test_flow.JWT import JWTBuilder
from test_flow.NVI import NVI
from test_flow.OAuth import OAuth
from test_flow.PRS import PRS
from test_flow.nvi_flows.delete import delete
from test_flow.nvi_flows.delete_by_id import delete_by_id
from test_flow.nvi_flows.get_by_id import get_by_id
from test_flow.nvi_flows.localize import localize
from test_flow.nvi_flows.query_referrals import query_referrals
from test_flow.nvi_flows.register import register
from test_flow.data import (
    SINGING_CERT_PATH,
    SINGING_KEY_PATH,
    MTLS_CERT_PATH,
    MTLS_KEY_PATH,
    NVI_ENDPOINT,
    OAUTH_ENDPOINT,
    PRS_ENDPOINT,
    VERIFY_CA_PATH,
)


def main(arg: str, kwargs: Dict[str, Any]) -> None:
    jwt_builder = JWTBuilder(
        token_url=f"{OAUTH_ENDPOINT}/oauth/token",
        mtls_cert_path=MTLS_CERT_PATH,
        signing_cert_path=SINGING_CERT_PATH,
        signing_key_path=SINGING_KEY_PATH,
    )
    oauth_service = OAuth(
        endpoint=OAUTH_ENDPOINT,
        mtls_cert=MTLS_CERT_PATH,
        mtls_key=MTLS_KEY_PATH,
        verify_ca=VERIFY_CA_PATH,
        jwt_builder=jwt_builder,
    )
    prs_service = PRS(
        endpoint=PRS_ENDPOINT,
        mtls_cert=MTLS_CERT_PATH,
        mtls_key=MTLS_KEY_PATH,
        verify_ca=VERIFY_CA_PATH,
    )
    nvi_service = NVI(
        endpoint=NVI_ENDPOINT,
        mtls_cert=MTLS_CERT_PATH,
        mtls_key=MTLS_KEY_PATH,
        verify_ca=VERIFY_CA_PATH,
    )
    match arg:
        case "register":
            register(
                oauth_service=oauth_service,
                prs_service=prs_service,
                nvi_service=nvi_service,
                bsn=kwargs["bsn"],
                care_context=kwargs["care_context"],
            )
        case "query":
            query_referrals(
                oauth_service=oauth_service,
                prs_service=prs_service,
                nvi_service=nvi_service,
                bsn=kwargs.get("bsn"),
                care_context=kwargs.get("care_context"),
            )
        case "get_by_id":
            get_by_id(
                oauth_service=oauth_service,
                nvi_service=nvi_service,
                reference_id=kwargs["reference_id"],
            )
        case "delete":
            delete(
                oauth_service=oauth_service,
                prs_service=prs_service,
                nvi_service=nvi_service,
                bsn=kwargs.get("bsn"),
                care_context=kwargs.get("care_context"),
            )
        case "delete_by_id":
            delete_by_id(
                oauth_service=oauth_service,
                nvi_service=nvi_service,
                reference_id=kwargs["reference_id"],
            )
        case "localize":
            localize(
                oauth_service=oauth_service,
                prs_service=prs_service,
                nvi_service=nvi_service,
                bsn=kwargs["bsn"],
                care_context=kwargs["care_context"],
                source_type=kwargs.get("source_type"),
            )
        case _:
            print(f"Unknown argument: {arg}")
            print("Valid arguments are: register, query, get_by_id, delete, delete_by_id, localize")
            print("Optionally provide parameters as key=value pairs.")
            print("Usage: ")
            print("register bsn=<bsn> care_context=<care_context>")
            print("query [bsn=<bsn>] [care_context=<care_context>]")
            print("get_by_id reference_id=<reference_id>")
            print("delete [bsn=<bsn>] [care_context=<care_context>]")
            print("delete_by_id reference_id=<reference_id>")
            print("localize bsn=<bsn> care_context=<care_context> [source_type=<source_type1,source_type2,...>]")
            raise SystemExit(2)


if __name__ == "__main__":
    import sys

    arguments = sys.argv[1:]
    if not arguments:
        print("Usage: python base.py <command> [key=value ...]")
        print("Valid commands: register, query, get_by_id, delete, delete_by_id, localize")
        raise SystemExit(2)
    arg = arguments[0]
    kwargs = {}
    for argument in arguments[1:]:
        key, value = argument.split("=")
        kwargs[key] = value
    main(arg, kwargs)
