from typing import Any, Dict

from test_flow.data import (
    MTLS_CERT_PATH,
    MTLS_KEY_PATH,
    NVI_ENDPOINT,
    OAUTH_ENDPOINT,
    PRS_ENDPOINT,
    SINGING_CERT_PATH,
    SINGING_KEY_PATH,
    VERIFY_CA_PATH,
)
from test_flow.JWT import JWTBuilder
from test_flow.NVI import NVI
from test_flow.nvi_flows.bundle_list_transaction import bundle_list_transaction
from test_flow.nvi_flows.create_list import create_list
from test_flow.nvi_flows.delete import delete
from test_flow.nvi_flows.delete_by_id import delete_by_id
from test_flow.nvi_flows.delete_list import delete_list
from test_flow.nvi_flows.get_by_id import get_by_id
from test_flow.nvi_flows.get_list_by_id import get_list_by_id
from test_flow.nvi_flows.localize import localize
from test_flow.nvi_flows.query_list import query_list
from test_flow.nvi_flows.query_referrals import query_referrals
from test_flow.nvi_flows.register import register
from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth
from test_flow.PRS import PRS


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
    nvi_list_service = NVIList(
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
        case "create_list":
            create_list(
                oauth_service=oauth_service,
                nvi_list_service=nvi_list_service,
                ura_number=kwargs["ura_number"],
                subject_system=kwargs["subject_system"],
                subject_value=kwargs["subject_value"],
                source_system=kwargs.get("source_system", "urn:ietf:rfc:3986"),
                source_value=kwargs.get("source_value", "EHR-SYS-2024-001"),
                code=kwargs["code"],
                display=kwargs.get("display", "Medicatieafspraak"),
            )
        case "query_list":
            query_list(
                prs_service=prs_service,
                oauth_service=oauth_service,
                nvi_list_service=nvi_list_service,
                bsn=kwargs.get("bsn"),
                care_context=kwargs.get("care_context"),
            )
        case "get_list_by_id":
            get_list_by_id(
                oauth_service=oauth_service,
                nvi_list_service=nvi_list_service,
                list_id=kwargs["list_id"],
            )
        case "delete_list":
            delete_list(
                oauth_service=oauth_service,
                nvi_list_service=nvi_list_service,
                list_id=kwargs.get("list_id"),
                subject_system=kwargs.get("subject_system"),
                subject_value=kwargs.get("subject_value"),
                source_system=kwargs.get("source_system"),
                source_value=kwargs.get("source_value"),
                code=kwargs.get("code"),
            )
        case "bundle_list_transaction":
            bundle_list_transaction(
                oauth_service=oauth_service,
                nvi_list_service=nvi_list_service,
                ura_number=kwargs["ura_number"],
                subject_system=kwargs["subject_system"],
                subject_value=kwargs["subject_value"],
                code=kwargs["code"],
                reference_id=kwargs["reference_id"],
                source_system=kwargs.get("source_system", "urn:ietf:rfc:3986"),
                source_value=kwargs.get("source_value", "EHR-SYS-2024-001"),
                display=kwargs.get("display", "Medicatieafspraak"),
            )
        case _:
            print(f"Unknown argument: {arg}")
            print(
                "Valid arguments are: register, query, get_by_id, delete, delete_by_id, localize, "
                "create_list, query_list, get_list_by_id, delete_list, bundle_list_transaction"
            )
            print("Optionally provide parameters as key=value pairs.")
            print("Usage: ")
            print("register bsn=<bsn> care_context=<care_context>")
            print("query [bsn=<bsn>] [care_context=<care_context>]")
            print("get_by_id reference_id=<reference_id>")
            print("delete [bsn=<bsn>] [care_context=<care_context>]")
            print("delete_by_id reference_id=<reference_id>")
            print("localize bsn=<bsn> care_context=<care_context> [source_type=<source_type1,source_type2,...>]")
            print(
                "create_list ura_number=<ura_number> subject_system=<system> subject_value=<value> code=<code> "
                "[source_system=<system>] [source_value=<value>] [display=<text>]"
            )
            print(
                "query_list [subject_system=<system>] [subject_value=<value>] [source_system=<system>] "
                "[source_value=<value>] [code=<code>]"
            )
            print("get_list_by_id list_id=<list_id>")
            print(
                "delete_list [list_id=<list_id>] [subject_system=<system>] [subject_value=<value>] "
                "[source_system=<system>] [source_value=<value>] [code=<code>]"
            )
            print(
                "bundle_list_transaction ura_number=<ura_number> subject_system=<system> subject_value=<value> "
                "code=<code> reference_id=<list_id> [source_system=<system>] [source_value=<value>] [display=<text>]"
            )
            raise SystemExit(2)


if __name__ == "__main__":
    import sys

    arguments = sys.argv[1:]
    if not arguments:
        print("Usage: python base.py <command> [key=value ...]")
        print(
            "Valid commands: register, query, get_by_id, delete, delete_by_id, localize, "
            "create_list, query_list, get_list_by_id, delete_list, bundle_list_transaction"
        )
        raise SystemExit(2)
    arg = arguments[0]
    kwargs = {}
    for argument in arguments[1:]:
        key, value = argument.split("=")
        kwargs[key] = value
    main(arg, kwargs)
