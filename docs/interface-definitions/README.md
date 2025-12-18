# Interface and Specifications

This documentation describes the interface definitions and use cases for the Nationale Verwijsindex Registratie Service (NVI-RS).

## Use cases and flows

The NVI-RS is used for referral registration. This process involves pseudonymization to ensure patient privacy. This is, however, omitted in the diagrams for simplicity but can be found in detail in the [Pseudonymization flow](./pseudonymization-flows.md) documentation.

- [**Registration**](#registration)

### Registration

There are three different types of ways the NVI-RS can register referrals in the NVI:

- [**Send data registration**](#send-data-registration)
- [**On-demand synchronization**](#on-demand-synchronization)
- [**Periodical synchronization**](#periodical-synchronization)

#### Send data registration

In this flow, a user manually uploads a FHIR resource with patient reference to the NVI-RS, which parses it and on success sends one create referral request to the NVI.
  
![Manual registration flow](../images/manual-registration.svg)

#### On-demand synchronization

In this flow, a user manually triggers the synchronization of one or more resource types, the NVI-RS pulls the requested resources from a FHIR store and registers them in the NVI.

![On-demand synchronization flow](../images/on-demand-sync.svg)

#### Periodical synchronization

In this flow, the NVI-RS periodically synchronizes referrals from a FHIR store and registers them in the NVI as a background task. A user can start or stop the scheduler manually.

![Periodical synchronization flow](../images/periodical-sync.svg)

## Api definitions

For API definitions and specifications, please refer to the Swagger documentation available at `/docs` endpoint of the running application or the `/openapi.json` endpoint for the raw OpenAPI specification.
