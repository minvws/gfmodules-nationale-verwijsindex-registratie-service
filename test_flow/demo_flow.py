# Flow from POV from ketenpartij (An NVI-Referral-Manager instance)

# MAIN Steps:
####### Step 1: Request OPRF token at PRS #######
# PRS uses OAuth, so we need to get an access token first
# a. Get OAuth access token using client credentials
# b. Request OPRF token for specific BSN using access token

####### Step 2: Work with FHIR List entries at NVI #######
# NVI uses OAuth, so each operation needs an access token

import base64
import json
from typing import Any

from test_flow.data import (
    CODE_CODING_SYSTEM,
    KETENPARTIJ_URA_NUMBER,
    MTLS_CERT_PATH,
    MTLS_KEY_PATH,
    NVI_API_ENDPOINT,
    NVI_OAUTH_ENDPOINT,
    NVI_URA_NUMBER,
    PRS_API_ENDPOINT,
    PRS_OAUTH_ENDPOINT,
    SUBJECT_IDENTIFIER_SYSTEM,
    TO_BE_REGISTERED_BSN,
    VERIFY_CA_PATH,
)
from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth
from test_flow.OPRF import OPRF
from test_flow.PRS import PRS

# 1-    OAth flow:
#           a- retrieve a bearer token with proper sub
# 2-    PRS Flow:
#           a- OAuth flow (Target PRS)
#           b- blind data (oprf)
#           c- exchange/eval
# 3-    NVI FHIR List flow:
#           a- OAuth flow (target NVI)
#           b- create, retrieve, query, delete, or transact on List entries


class DemoFlow:
    def __init__(
        self,
    ) -> None:
        self.nvi_list = NVIList(NVI_API_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH)

        self.prs_oauth = OAuth(
            endpoint=PRS_OAUTH_ENDPOINT,
            mtls_cert=MTLS_CERT_PATH,
            mtls_key=MTLS_KEY_PATH,
            verify_ca=VERIFY_CA_PATH,
            target_audience=PRS_API_ENDPOINT,
        )
        self.nvi_oauth = OAuth(
            endpoint=NVI_OAUTH_ENDPOINT,
            mtls_cert=MTLS_CERT_PATH,
            mtls_key=MTLS_KEY_PATH,
            verify_ca=VERIFY_CA_PATH,
            target_audience=NVI_API_ENDPOINT,
        )
        self.prs = PRS(PRS_API_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH)

    def step_1_request_oprf_token(self, value=TO_BE_REGISTERED_BSN) -> tuple[str, str]:
        """
        Step 1: Request OPRF token at PRS.
        Returns blind_factor and oprf_jwe.
        """
        bearer_token = self.prs_oauth.get_bearer_token(scope="prs:oprf")
        blind_factor, blinded_input = OPRF.create_blinded_input(
            personal_identifier={
                "landCode": "NL",
                "type": "BSN",
                "value": value,
            },
            recipient_organization="ura:" + NVI_URA_NUMBER,
            recipient_scope="nationale-verwijsindex",
        )
        oprf_jwe = self.prs.evaluate_oprf(
            blinded_input=blinded_input,
            bearer_token=bearer_token,
            recepient_org=f"ura:{NVI_URA_NUMBER}",
        )
        return blind_factor, oprf_jwe

    @staticmethod
    def _encode_subject_identifier(oprf_jwe: str, blind_factor: str) -> str:
        payload = {
            "evaluated_output": oprf_jwe,
            "blind_factor": blind_factor,
        }
        payload_json = json.dumps(payload).encode("utf-8")
        return base64.urlsafe_b64encode(payload_json).decode("ascii")

    def step_2_create_list_entry(
        self,
        blind_factor: str,
        oprf_jwe: str,
        code: str = "Genomics",
    ) -> Any:
        """
        Step 2: Create a FHIR List entry in NVI.
        """
        subject_identifier = self._encode_subject_identifier(
            oprf_jwe=oprf_jwe,
            blind_factor=blind_factor,
        )
        bearer_token = self.nvi_oauth.get_bearer_token(scope="epd:write")
        body = {
            "resourceType": "List",
            "extension": [
                {
                    "valueReference": {
                        "identifier": {
                            "system": "http://fhir.nl/fhir/NamingSystem/ura",
                            "value": KETENPARTIJ_URA_NUMBER,
                        }
                    },
                    "url": "http://minvws.github.io/generiekefuncties-docs/StructureDefinition/nl-gf-localization-custodian",
                }
            ],
            "subject": {
                "identifier": {
                    "system": SUBJECT_IDENTIFIER_SYSTEM,
                    "value": subject_identifier,
                }
            },
            "source": {
                "identifier": {
                    "system": "urn:ietf:rfc:3986",
                    "value": "EHR-SYS-2024-001",
                },
                "type": "Device",
            },
            "status": "current",
            "mode": "working",
            "emptyReason": {
                "coding": [
                    {
                        "code": "withheld",
                        "system": "http://terminology.hl7.org/CodeSystem/list-empty-reason",
                    }
                ]
            },
            "code": {
                "coding": [
                    {
                        "code": code,
                        "system": CODE_CODING_SYSTEM,
                        "display": "Medicatieafspraak",
                    }
                ]
            },
        }
        return self.nvi_list.create(body=body, bearer_token=bearer_token)

    def step_3_get_list_entry_by_id(self, list_id: str) -> Any:
        """
        Step 3: Get a FHIR List entry by ID.
        """
        bearer_token = self.nvi_oauth.get_bearer_token(scope="epd:read")
        return self.nvi_list.get_by_id(list_id=list_id, bearer_token=bearer_token)

    def step_4_query_list_entries(
        self,
        blind_factor: str,
        oprf_jwe: str,
        code: str = "Genomics",
    ) -> Any:
        """
        Step 4: Query FHIR List entries.
        """
        subject_identifier = self._encode_subject_identifier(
            oprf_jwe=oprf_jwe,
            blind_factor=blind_factor,
        )
        bearer_token = self.nvi_oauth.get_bearer_token(scope="epd:read")
        return self.nvi_list.query(
            bearer_token=bearer_token,
            subject_system=SUBJECT_IDENTIFIER_SYSTEM,
            subject_value=subject_identifier,
            code=code,
        )

    def step_5_delete_list_entry_by_id(self, list_id: str) -> int:
        """
        Step 5: Delete a FHIR List entry by ID.
        """
        bearer_token = self.nvi_oauth.get_bearer_token(scope="epd:write")
        return self.nvi_list.delete_by_id(list_id=list_id, bearer_token=bearer_token)

    def step_6_list_transaction_bundle(self, subject_identifier: str, reference_id: str) -> Any:
        """
        Step 6: Execute a FHIR transaction bundle for List operations.
        """
        bearer_token = self.nvi_oauth.get_bearer_token(scope="epd:write")
        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "request": {"method": "POST", "url": "List"},
                    "resource": {
                        "resourceType": "List",
                        "extension": [
                            {
                                "valueReference": {
                                    "identifier": {
                                        "system": "http://fhir.nl/fhir/NamingSystem/ura",
                                        "value": KETENPARTIJ_URA_NUMBER,
                                    }
                                },
                                "url": "http://minvws.github.io/generiekefuncties-docs/StructureDefinition/nl-gf-localization-custodian",
                            }
                        ],
                        "subject": {
                            "identifier": {
                                "system": SUBJECT_IDENTIFIER_SYSTEM,
                                "value": subject_identifier,
                            }
                        },
                        "source": {
                            "identifier": {
                                "system": "urn:ietf:rfc:3986",
                                "value": "EHR-SYS-2024-001",
                            },
                            "type": "Device",
                        },
                        "status": "current",
                        "mode": "working",
                        "emptyReason": {
                            "coding": [
                                {
                                    "code": "withheld",
                                    "system": "http://terminology.hl7.org/CodeSystem/list-empty-reason",
                                }
                            ]
                        },
                        "code": {
                            "coding": [
                                {
                                    "code": "Genomics",
                                    "system": CODE_CODING_SYSTEM,
                                    "display": "Medicatieafspraak",
                                }
                            ]
                        },
                    },
                },
                {"request": {"method": "GET", "url": f"List/{reference_id}"}},
                {
                    "request": {
                        "method": "GET",
                        "url": f"List?patient.identifier={SUBJECT_IDENTIFIER_SYSTEM}|{subject_identifier}&code=Genomics",
                    }
                },
                {"request": {"method": "DELETE", "url": f"List/{reference_id}"}},
            ],
        }
        return self.nvi_list.transaction(bundle=bundle, bearer_token=bearer_token)


if __name__ == "__main__":
    demo_flow = DemoFlow()

    blind_factor, oprf_jwe = demo_flow.step_1_request_oprf_token()

    created_list = demo_flow.step_2_create_list_entry(
        blind_factor=blind_factor,
        oprf_jwe=oprf_jwe,
    )
    print("Created list entry:")
    print(created_list)

    if "id" in created_list:
        list_id = created_list["id"]
        listed = demo_flow.step_3_get_list_entry_by_id(list_id=list_id)
        print("Fetched list entry:")
        print(listed)

        queried = demo_flow.step_4_query_list_entries(
            blind_factor=blind_factor,
            oprf_jwe=oprf_jwe,
        )
        print("Queried list entries:")
        print(queried)

        deleted_status = demo_flow.step_5_delete_list_entry_by_id(list_id=list_id)
        print("Deleted list entry status:")
        print(deleted_status)
