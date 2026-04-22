import base64
import json

from test_flow.data import (
    CODE_CODING_SYSTEM,
    NVI_ENDPOINT,
    NVI_URA_NUMBER,
    PRS_ENDPOINT,
    SOURCE_IDENTIFIER_SYSTEM,
    SUBJECT_IDENTIFIER_SYSTEM,
)
from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth
from test_flow.OPRF import OPRF
from test_flow.PRS import PRS


def create_list(
    nvi_list_service: NVIList,
    ura_number: str,
    source: str,
    subject: str,
    code: str,
    display: str,
) -> None:
    body = {
        "resourceType": "List",
        "extension": [
            {
                "valueReference": {
                    "identifier": {
                        "system": "http://fhir.nl/fhir/NamingSystem/ura",
                        "value": ura_number,
                    }
                },
                "url": "http://minvws.github.io/generiekefuncties-docs/StructureDefinition/nl-gf-localization-custodian",
            }
        ],
        "subject": {
            "identifier": {
                "system": SUBJECT_IDENTIFIER_SYSTEM,
                "value": subject,
            }
        },
        "source": {
            "identifier": {
                "system": SOURCE_IDENTIFIER_SYSTEM,
                "value": source,
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
                    "display": display,
                }
            ]
        },
    }

    nvi_token = oauth_service.get_bearer_token(scope="epd:write", target_audience=NVI_ENDPOINT, with_jwt=True)
    created = nvi_list_service.create(body=body, bearer_token=nvi_token)
    print("Created list entry:")
    print(created)
