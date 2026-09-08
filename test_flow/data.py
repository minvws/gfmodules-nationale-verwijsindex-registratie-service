# Connection constants
PRS_ENDPOINT = "https://pseudoniemendienst.proeftuin.gf.irealisatie.nl/v0.2"
PRS_OAUTH_ENDPOINT = f"{PRS_ENDPOINT}/oauth"
PRS_API_ENDPOINT = f"{PRS_ENDPOINT}/api"
NVI_ENDPOINT = "https://nvi.proeftuin.gf.irealisatie.nl/v0.2"
NVI_OAUTH_ENDPOINT = f"{NVI_ENDPOINT}/oauth"
NVI_API_ENDPOINT = f"{NVI_ENDPOINT}/api"
MTLS_CERT_PATH = "/path/to/my-oin-cert-with-chain.crt"
MTLS_KEY_PATH = "/path/to/my-oin.key"
# VERIFY_CA_PATH = "/path/to/ca.pem"
VERIFY_CA_PATH = True

# Demo constants
NVI_URA_NUMBER = "90000901"
KETENPARTIJ_URA_NUMBER = "90000002"
TO_BE_REGISTERED_BSN = "999990007"

SOURCE_IDENTIFIER_SYSTEM = "urn:ietf:rfc:3986"
SUBJECT_IDENTIFIER_SYSTEM = "http://minvws.github.io/generiekefuncties-docs/NamingSystem/nvi-identifier"
CODE_CODING_SYSTEM = "http://minvws.github.io/generiekefuncties-docs/CodeSystem/nl-gf-data-categories-cs"
