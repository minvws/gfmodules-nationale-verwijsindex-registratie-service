# Flow from POV from ketenpartij (An NVI-Referral-Manager instance)

# MAIN Steps:
####### Step 1: Request OPRF token at PRS #######
# PRS uses OAuth, so we need to get an access token first
# a. Get OAuth access token using client credentials
# b. Request OPRF token for specific BSN using access token

####### Step 2: Register Referral at NVI #######
# NVI also uses OAuth, so we need to get an access token first
# a. Get OAuth access token using client credentials
# b. Register Referral using access token and OPRF token

####### Step 3: Query status of Referral at NVI #######
# a. Get OAuth access token using client credentials
# b. Query status of Referral using access token

import base64
import json
from typing import Any

from test_flow.data import (
    CODE_CODING_SYSTEM,
    KETENPARTIJ_ORGANIZATION_TYPE,
    KETENPARTIJ_URA_NUMBER,
    MTLS_CERT_PATH,
    MTLS_KEY_PATH,
    NVI_ENDPOINT,
    NVI_URA_NUMBER,
    OAUTH_ENDPOINT,
    PRS_ENDPOINT,
    SINGING_CERT_PATH,
    SINGING_KEY_PATH,
    SUBJECT_IDENTIFIER_SYSTEM,
    TO_BE_REGISTERED_BSN,
    TO_BE_REGISTERED_CARE_CONTEXT,
    VERIFY_CA_PATH,
)
from test_flow.JWT import JWTBuilder
from test_flow.NVI import NVI
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
# 3-    NVI Reference registration:
#           a- OAuth flow
#           b- prs flow
#           c- register a reference for 1 patient
# 4-    retrieve data for an org:
#           a- OAuth (target NVI)
#           c- retrieve data for client URA number
#
# 5-    retrieve all references for a specific Patient and careContext:
#           a- OAuth (target NVI)
#           b- PRS flow
#           c- retrieve data for a client (pseudonym + client URA)
#
# 6-    delete all references for client URA:
#           a- OAuth (target NVI)
#           b- delete all refs for URA
#
# 7-    delete all references for a specific patient:
#           a- OAuth (target NVI)
#           b- PRS flow
#           c- delete all refs for a specific patient (no care context)
#
# 8-    delete all refs for a specific record:
#           a- OAuth (targeet NVI)
#           b- PRS flow
#           c- delete specific ref (with care context)
#
# 9-    Loccalise a patient:
#           a- OAuth (target NVI)
#           b- PRS flow
#           c- localise using proper Parameters (FHIR)


class DemoFlow:
    def __init__(
        self,
    ) -> None:
        self.nvi = NVI(NVI_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH)
        self.nvi_list = NVIList(NVI_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH)
        jwt_builder = JWTBuilder(
            token_url=f"{OAUTH_ENDPOINT}/oauth/token",
            mtls_cert_path=MTLS_CERT_PATH,
            signing_cert_path=SINGING_CERT_PATH,
            signing_key_path=SINGING_KEY_PATH,
        )
        self.oauth = OAuth(OAUTH_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH, jwt_builder)
        self.prs = PRS(PRS_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH)

    def step_1_request_oprf_token(self, value=TO_BE_REGISTERED_BSN) -> tuple[str, str]:
        """
        Step 1: Request OPRF token at PRS.
        Returns blind_factor and oprf_jwe.
        """
        bearer_token = self.oauth.get_bearer_token(
            scope="prs:read",
            target_audience=PRS_ENDPOINT,
            with_jwt=True,
        )
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

    def step_2_register_referral(self, pseudonym: str, blind_factor: str) -> Any:
        """
        Step 2: Register Referral at NVI.
        Returns the NVI registration response.
        """
        bearer_token = self.oauth.get_bearer_token(
            scope="epd:write",
            target_audience=NVI_ENDPOINT,
            with_jwt=True,
        )
        response = self.nvi.register(
            ura_number=KETENPARTIJ_URA_NUMBER,
            bearer_token=bearer_token,
            source_type=KETENPARTIJ_ORGANIZATION_TYPE,
            pseudonym=pseudonym,
            oprf_key=blind_factor,
            care_context=TO_BE_REGISTERED_CARE_CONTEXT,
        )
        return response

    @staticmethod
    def _encode_subject_identifier(oprf_jwe: str, blind_factor: str) -> str:
        payload = {
            "evaluated_output": oprf_jwe,
            "blind_factor": blind_factor,
        }
        payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(payload_json).decode("ascii")

    def step_3_create_list_entry(
        self,
        blind_factor: str,
        oprf_jwe: str,
        code: str = "Genomics",
    ) -> Any:
        """
        Step 3: Create a FHIR List entry in NVI.
        """
        subject_identifier = self._encode_subject_identifier(
            oprf_jwe=oprf_jwe,
            blind_factor=blind_factor,
        )
        bearer_token = self.oauth.get_bearer_token(
            scope="epd:write",
            target_audience=NVI_ENDPOINT,
            with_jwt=True,
        )
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

    def step_4_get_list_entry_by_id(self, list_id: str) -> Any:
        """
        Step 4: Get a FHIR List entry by ID.
        """
        bearer_token = self.oauth.get_bearer_token(
            scope="epd:read",
            target_audience=NVI_ENDPOINT,
            with_jwt=True,
        )
        return self.nvi_list.get_by_id(list_id=list_id, bearer_token=bearer_token)

    def step_5_query_list_entries(
        self,
        blind_factor: str,
        oprf_jwe: str,
        code: str = "Genomics",
    ) -> Any:
        """
        Step 5: Query FHIR List entries.
        """
        subject_identifier = self._encode_subject_identifier(
            oprf_jwe=oprf_jwe,
            blind_factor=blind_factor,
        )
        bearer_token = self.oauth.get_bearer_token(
            scope="epd:read",
            target_audience=NVI_ENDPOINT,
            with_jwt=True,
        )
        return self.nvi_list.query(
            bearer_token=bearer_token,
            subject_system=SUBJECT_IDENTIFIER_SYSTEM,
            subject_value=subject_identifier,
            code=code,
        )

    def step_6_delete_list_entry_by_id(self, list_id: str) -> int:
        """
        Step 6: Delete a FHIR List entry by ID.
        """
        bearer_token = self.oauth.get_bearer_token(
            scope="epd:write",
            target_audience=NVI_ENDPOINT,
            with_jwt=True,
        )
        return self.nvi_list.delete_by_id(list_id=list_id, bearer_token=bearer_token)

    def step_7_list_transaction_bundle(self, subject_identifier: str, reference_id: str) -> Any:
        """
        Step 7: Execute a FHIR transaction bundle for List operations.
        """
        bearer_token = self.oauth.get_bearer_token(
            scope="epd:write",
            target_audience=NVI_ENDPOINT,
            with_jwt=True,
        )
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

    registered_data_reference = demo_flow.step_2_register_referral(pseudonym=oprf_jwe, blind_factor=blind_factor)
    print("Registered data reference:")
    print(registered_data_reference)

    created_list = demo_flow.step_3_create_list_entry(
        blind_factor=blind_factor,
        oprf_jwe=oprf_jwe,
    )
    print("Created list entry:")
    print(created_list)

    if "id" in created_list:
        list_id = created_list["id"]
        listed = demo_flow.step_4_get_list_entry_by_id(list_id=list_id)
        print("Fetched list entry:")
        print(listed)

        queried = demo_flow.step_5_query_list_entries(
            blind_factor=blind_factor,
            oprf_jwe=oprf_jwe,
        )
        print("Queried list entries:")
        print(queried)

        deleted_status = demo_flow.step_6_delete_list_entry_by_id(list_id=list_id)
        print("Deleted list entry status:")
        print(deleted_status)
