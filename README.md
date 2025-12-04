# Nationale Verwijsindex Registratie Service

This app is the Nationale Verwijsindex Registratie Service (NVI-RS) and is part of the 'Generieke Functies, lokalisatie en addressering' project of the Ministry of Health, Welfare and Sport of the Dutch government. The purpose of this application is to pull and push referrals read from FHIR stores to the Nationale Verwijs Index (NVI), which stores referrals in the register that associates a Health Provider with pseudonym and data domain.

> [!CAUTION]
> ## Disclaimer
> This project and all associated code serve solely as **documentation and demonstration purposes**
> to illustrate potential system communication patterns and architectures.
>
> This codebase:
>
> - Is NOT intended for production use
> - Does NOT represent a final specification
> - Should NOT be considered feature-complete or secure
> - May contain errors, omissions, or oversimplified implementations
> - Has NOT been tested or hardened for real-world scenarios
>
> The code examples are *only* meant to help understand concepts and demonstrate possibilities.
>
> By using or referencing this code, you acknowledge that you do so at your own risk and that
> the authors assume no liability for any consequences of its use.

## Setup

The application is a FastAPI application, so you can use the [FastAPI documentation](https://fastapi.tiangolo.com/) to see how to use the application.
In order for the application to run properly, a few external components needs to be setup:

### Nationale Verwijs Index

The NVI-RS connects to the [NVI](https://github.com/minvws/gfmodules-national-referral-index) to register the referrals. Depending on the environment of the 'Registratie service' it needs to connect to either a hosted (eq. production or test) NVI or a local NVI.

The connection to the NVI **MUST** be established with an UZI Server Certificate. See section [Connecting with an UZI Server Certificate](#connecting-with-an-uzi-server-certificate) on how to obtain such a certificate.

On bootstrap, the app will look for the URA number associated with the certificate, then it will start. An Example of the full
setup with mock certificates script can be found in [gfmodules-coordination-repo](https://github.com/minvws/gfmodules-coordination),
where a certificates generation [script](https://github.com/minvws/gfmodules-coordination/blob/main/tools/generate_certs.sh) will allocate certificates accordingly.

You can find related configuration properties for NVI in the [app.conf.example file](app.conf.example) in the `[referral_api]` section.

> [!IMPORTANT]
> It is important to note that the URA number in the certificate needs to match the FHIR Store which the application
> is pulling data from and register in the NVI.

### Pseudoniemendienst

The NVI-RS requires a [pseudonymization service](https://github.com/minvws/gfmodules-pseudoniemendienst) in order for it to work. The PRS is used to create safe and secure pseudonyms to communicate with the NVI and OTV.
You can find related configuration properties in the [app.conf.example file](app.conf.example) in the `[pseudonym_api]` section.

The connection to the PRS **MUST** be established with an UZI Server Certificate. See section [Connecting with an UZI Server Certificate](#connecting-with-an-uzi-server-certificate) on how to obtain such a certificate.

### OTV

The NVI-RS also uses an permission service, also called the online-toestemmingsvoorziening-portaal (OTV). The OTV is used to check if Patients have given consent for sharing their registered referral with a certain organization. The NVI-RS is set up to use the [OTV-stub](https://github.com/minvws/gfmodules-online-toestemmingsvoorziening-portaal-stub). You can find related configuration properties in the [app.conf.example file](app.conf.example) in the `[otv_stub_api]` section.

The GFmodules OTV-stub does not require mutual TLS authentication, but in order to create OTV-specific pseudonyms the URA number of the OTV needs to be known. For this either an UZI server certificate or an hardcoded URA needs to be present. See the `[otv_stub_certificate]` section in the [app.conf.example file](app.conf.example) for more information.

### FHIR Store

In order to make use of the polling feature, a connection to a FHIR store like [HAPI](https://hapi.fhir.org/) for example needs
to be established. You can find the related configuration properties in the [app.conf.example file](app.conf.example) in the `[metadata_api]` section.

## Development

### Local (Poetry)

1. Install [Python ^3.11](https://www.python.org/downloads/release/python-3110/)
2. Install [Poetry](https://python-poetry.org/docs/#installation).
3. Install dependencies:

```bash
poetry install
```

4. Create a copy of the example configuration

The application uses a config file for storing configuration. For local development, you can copy the example configuration:

```bash
cp app.conf.example app.conf
```

This copies the example configuration to `app.conf`.

5. Run the application:

```bash
poetry run python -m app.main
```

### Docker

Build and run with Docker Compose:

```bash
docker compose up -d
```

Then you can access the served app at [http://localhost:8515](http://localhost:8515) and the swagger documentation at [http://localhost:8515/docs](http://localhost:8515/docs).

Or build manually:

#### Docker container builds

There are two ways to build a docker container from this application. The first is the default mode created with:

```bash
docker build \
  --build-arg="NEW_UID=1000" \
  --build-arg="NEW_GID=1000" \
  -f docker/Dockerfile \
  -t gfmodules-nationale-verwijsindex-registratie-service \
  .
```

This will build a docker container that will run its migrations to the database specified in app.conf.

The second mode is a "standalone" mode, where it will not run migrations, and where you must explicitly specify
an app.conf mount.

```bash
docker build \
  --build-arg="standalone=true" \
  -f docker/Dockerfile \
  -t gfmodules-nationale-verwijsindex-registratie-service \
  .
```

Both containers only differ in their init script and the default version usually will mount its own local src directory
into the container's /src dir.

```bash
docker run -ti --rm -p 8515:8515 \
  --mount type=bind,source=./app.conf.example,target=/src/app.conf \
  gfmodules-nationale-verwijsindex-registratie-service
```

## Interface and Specifications definitions

See [Interface and Specifications](docs/interface-definitions/README.md)

## Scheduled referral registration

The application can be configured to periodically pull referrals from the FHIR store and register them in the NVI.
This feature can be enabled by setting the values under `[scheduler]` in the config file, specifically `automatic_background_update` to `true`.

When enabled, the application will run a background job at intervals specified by the `scheduled_delay` setting.

See the [interface-definitions](#interface-and-specifications-definitions) for more information on the API endpoints available to start or stop synchronization manually.

## Connecting with an UZI Server Certificate

Some services that the application connects to, such as the NVI and PRS, require mutual TLS authentication using [UZI Server Certificates](https://www.uziregister.nl/softwareleveranciers/testmiddelen-en-testomgeving). To establish a secure connection, you must obtain an UZI Server Certificate from the UZI Register.

To request a test set with UZI server certificates see section [Testset met servercertificaat](https://www.uziregister.nl/documenten/2019/07/12/testset-met-servercertificaat).

## Supported data domains

The NVI-RS is built to be able to register referrals from a large number of data domains. Currently the resources types listed in the [ReferenceParser](https://github.com/minvws/gfmodules-nationale-verwijsindex-registratie-service-private/blob/main/app/services/parsers/reference.py#L35) are supported. These domains are `FHIR` resource types holding a `Patient` reference that can be registered in the NVI.

By default, the application enables synchronization on the following data domains:

- `ImagingStudy`
- `MedicationStatement`

The enabled synchronization data domains can however be modified by changing the `data_domains` setting in the `[app]` section in the [configuration file](app.conf.example)

## Installation

Docker images are published to the [GitHub Container Registry](https://ghcr.io/minvws/gfmodules-nationale-verwijsindex-registratie-service)

You can pull the latest image with the following command:

```bash
docker pull ghcr.io/minvws/gfmodules-nationale-verwijsindex-registratie-service:latest
```

## Contribution

As stated in the [disclaimer](#disclaimer) this project and all associated code serve solely as documentation and
demonstration purposes to illustrate potential system communication patterns and architectures.

For that reason we will only accept contributions that fit this goal. We do appreciate any effort from the
community, but because our time is limited it is possible that your PR or issue is closed without a full justification.

If you plan to make non-trivial changes, we recommend to open an issue beforehand where we can discuss your planned changes. This increases the chance that we might be able to use your contribution (or it avoids doing work if there are reasons why we wouldn't be able to use it).

Note that all commits should be signed using a gpg key.
