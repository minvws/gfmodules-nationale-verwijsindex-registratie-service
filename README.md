# NVI Referral Manager

This app is the NVI referral manager and is part of the 'Generieke Functies, lokalisatie en addressering' project of the Ministry of Health, Welfare and Sport of the Dutch government. The purpose of this application is to pull and push referrals read from FHIR stores to the National Referral Index, which stores referrals in the register that associates a Health Provider with pseudonym and data domain.

## Disclaimer

This project and all associated code serve solely as documentation
and demonstration purposes to illustrate potential system
communication patterns and architectures.

This codebase:

- Is NOT intended for production use
- Does NOT represent a final specification
- Should NOT be considered feature-complete or secure
- May contain errors, omissions, or oversimplified implementations
- Has NOT been tested or hardened for real-world scenarios

The code examples are only meant to help understand concepts and demonstrate possibilities.

By using or referencing this code, you acknowledge that you do so at your own
risk and that the authors assume no liability for any consequences of its use.

## Setup

To ensure this application functions properly, make sure the [NVI service](https://github.com/minvws/gfmodules-nvi-referral-manager-private), the [PRS-stub](https://github.com/minvws/gfmodules-pseudonym-stub-private/), and a FHIR store (e.g. [HAPI](https://hapi.fhir.org/)) are running and accessible.
The application is a FastAPI application, so you can use the [FastAPI documentation](https://fastapi.tiangolo.com/) to see how to use the application.

Run the referral manager via:

```bash
docker compose up -d
```

Then you can access the referral manager at [http://localhost:8515](http://localhost:8515) and the swagger documentation at [http://localhost:8515/docs](http://localhost:8515/docs).

URA number can be configured in the app.conf file. It should be set to the same URA as the one used in the NVI application.

## Installation

### Local (Poetry)

1. Install [Python ^3.11](https://www.python.org/downloads/release/python-3110/)
2. Install [Poetry](https://python-poetry.org/docs/#installation).
3. Install dependencies:

```bash
poetry install
```

4. Run the application:

```bash
poetry run python -m app.main
```

### Docker

Build and run with Docker Compose:

```bash
docker compose up -d
```

Or build manually:

#### Docker container builds

There are two ways to build a docker container from this application. The first is the default mode created with:

```bash
make container-build
```

This will build a docker container that will run its migrations to the database specified in app.conf.

The second mode is a "standalone" mode, where it will not generate migrations, and where you must explicitly specify
an app.conf mount.

```bash
make container-build-sa
```

Both containers only differ in their init script and the default version usually will mount its own local src directory
into the container's /src dir.

## API Endpoints

### Registration Endpoint

- **POST** `/registration`
  - Registers a new referral based on a FHIR CarePlan resource.
  - **Request body:** JSON (FHIR CarePlan)
  - **Response:** `201 Created` on success

### Health Endpoint

- **GET** `/health`
  - Returns health status of the service, and checks if the relevant APIs are reachable.
    - **Response:** JSON with health status per component.

### Synchronize Endpoint

- **POST** `/synchronize`
  - Triggers synchronization of all domains or for a specified domain.
  - **Response:** `200 OK` on success.

### Scheduler Endpoint

- **POST** `/scheduler/start`
  - Triggers the scheduler to run.
  - **Response:** `200 OK` on success.

- **POST** `/scheduler/stop`
  - Triggers the scheduler to stop.
  - **Response:** `200 OK` on success.

- **GET** `/scheduler/runners-history`
  - Returns the runners history of the scheduler.
  - **Response:** JSON with status information.

---

## Example request for registration

```bash
curl -X 'POST' \
  'http://localhost:8515/registration' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
        "resourceType": "CarePlan",
        "id": "default-31",
        "status": "completed",
        "intent": "plan",
        "title": "Random CarePlan",
        "description": "random description",
        "subject": {
          "reference": "Patient/default-1",
          "display": "Mohammed Koster",
          "type": "Patient",
          "identifier": 
            {
              "system": "http://fhir.nl/fhir/NamingSystem/bsn",
              "value": "468467543"
            }
        },
        "careTeam": [
          {
            "reference": "CareTeam/default-29",
            "display": "Care Team 1"
          },
          {
            "reference": "CareTeam/default-28",
            "display": "Care Team 2"
          }
        ]
      }'
```

## Contribution

As stated in the [Disclaimer](#disclaimer) this project and all associated code serve solely as documentation and
demonstration purposes to illustrate potential system communication patterns and architectures.

For that reason we will only accept contributions that fit this goal. We do appreciate any effort from the
community, but because our time is limited it is possible that your PR or issue is closed without a full justification.

If you plan to make non-trivial changes, we recommend to open an issue beforehand where we can discuss your planned changes. This increases the chance that we might be able to use your contribution (or it avoids doing work if there are reasons why we wouldn't be able to use it).

Note that all commits should be signed using a gpg key.
