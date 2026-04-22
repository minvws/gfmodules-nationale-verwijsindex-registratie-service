from test_flow.data import NVI_ENDPOINT, SOURCE_IDENTIFIER_SYSTEM, SUBJECT_IDENTIFIER_SYSTEM
from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth


def bundle_list_transaction(
    oauth_service: OAuth,
    nvi_list_service: NVIList,
    ura_number: str,
    subject: str,
    code: str,
    reference_id: str,
    source: str,
    display: str,
) -> None:
    print("Posting List transaction bundle")
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
                                "system": "http://minvws.github.io/generiekefuncties-docs/CodeSystem/nl-gf-data-categories-cs",
                                "display": display,
                            }
                        ]
                    },
                },
            },
            {
                "request": {
                    "method": "GET",
                    "url": f"List/{reference_id}",
                }
            },
            {
                "request": {
                    "method": "GET",
                    "url": f"List?patient.identifier={SUBJECT_IDENTIFIER_SYSTEM}|{subject}&code={code}",
                }
            },
            {
                "request": {
                    "method": "DELETE",
                    "url": f"List/{reference_id}",
                }
            },
        ],
    }
    nvi_token = oauth_service.get_bearer_token(scope="epd:write", target_audience=NVI_ENDPOINT, with_jwt=True)
    result = nvi_list_service.transaction(bundle=bundle, bearer_token=nvi_token)
    print("Transaction result:")
    print(result)
