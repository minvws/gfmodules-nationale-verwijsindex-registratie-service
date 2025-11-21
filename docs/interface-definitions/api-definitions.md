# API Endpoints

## Base URL

### GET `/`

Returns service name and version information.

**Response:**
Text with service name and version information.

### GET `/version.json`

Returns the content of the version file.

**Response:**
Content of the version file.

---

## Health

### GET `/health`

Returns health status of the service and checks if the relevant APIs are reachable.

**Response:**
JSON with health status per component.

---

## Registration

### POST `/registration`

Registers new referrals based on resources in a FHIR bundle.

**Request body:**
JSON (FHIR bundle)

**Response:**
`201 Created` on success.

---

## Synchronize

### POST `/synchronize`

Triggers synchronization of all domains or a specified domain.

**Response:**
`200 OK` on success.

---

## Scheduler

### POST `/scheduler/start`

Triggers the scheduler to run.

**Response:**
`200 OK` on success.

### POST `/scheduler/stop`

Triggers the scheduler to stop.

**Response:**
`200 OK` on success.

### GET `/scheduler/runners-history`

Returns the runner history of the scheduler.

**Response:**
JSON with status information.

---

## Authorization check

### POST `/authorize`

Checks if a patient has given permission to share referrals with a certain organization.

**Request body:**
JSON with encrypted patient identifier and organization identifier.

**Response:**
`200 OK` and authorization status.

---

## Example request for manual registration

```bash
curl -X 'POST' \
  'http://localhost:8515/registration' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "resourceType": "Bundle",
    "id": "bundle-1",
    "type": "collection",
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "example-1",
                "identifier": [
                    {
                        "system": "http://fhir.nl/fhir/NamingSystem/bsn",
                        "value": "950000012"
                    }
                ],
                "active": false,
                "name": [
                    {
                        "use": "usual",
                        "text": "Ize Borman",
                        "family": "Koster",
                        "given": [
                            "Mohammed"
                        ]
                    }
                ],
                "gender": "unknown",
                "birthDate": "1999-11-20",
                "address": [
                    {
                        "use": "home",
                        "type": "both",
                        "text": "Vigoboulevard 959, 6268FB Bunde, Utrecht Netherlands",
                        "line": [
                            "Vigoboulevard 959"
                        ],
                        "city": "Bunde",
                        "state": "Utrecht",
                        "postalCode": "6268FB",
                        "country": "Netherlands"
                    }
                ]
            },
            {
                "resource": {
                    "resourceType": "CarePlan",
                    "id": "example-1",
                    "status": "completed",
                    "intent": "plan",
                    "title": "Random CarePlan",
                    "description": "random description",
                    "subject": {
                        "reference": "Patient/example-1",
                    },
                    "careTeam": [
                        {
                            "reference": "CareTeam/example-1",
                            "display": "Care Team 1"
                        },
                        {
                            "reference": "CareTeam/example-2",
                            "display": "Care Team 2"
                        }
                    ]
                }
            }
        ]
    }'
```
