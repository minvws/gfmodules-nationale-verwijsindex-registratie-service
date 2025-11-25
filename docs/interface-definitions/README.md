# Interface and Specifications

This documentation describes the interface definitions and use cases for the Nationale Verwijsindex Registratie Service (NVI-RS).

## Use cases and flows

The NVI-RS use cases can be divided into two main categories: authorization check and referral registrations. The flows are described below.

Both processes involve pseudonymization to ensure patient privacy. This is, however, omitted in the diagrams for simplicity but can be found in detail in the [Pseudonymization flow](./pseudonymization-flows.md) documentation.

- [**Registration**](#registration)
- [**Authorization Check**](#authorization-check)

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

### Authorization Check

When checking if a patient has given permission to share referrals with a certain organization, the NVI-RS follows this pseudonymization flow:

1. **Receive request** - The NVI-RS receives a request containing the encrypted patient identifier and an organization identifier.
2. **Decrypt internal patient identifier** - The NVI-RS decrypts the internal patient identifier using its symmetric key.
3. **Fetch Patient from FHIR store** - The NVI-RS fetches the Patient resource from the FHIR store using the decrypted internal patient identifier.
4. **Extract BSN** - The Patient's BSN is extracted.
5. **Create reversible pseudonym** - The NVI referral requests a reversible pseudonym specific for the online-toestemmingsvoorziening(OTV) for the BSN from the Pseudoniemendienst (PRS).
6. **Check authorization** - The NVI-RS checks with the OTV if the patient has given permission to share referrals with the specified organization. This results in an authorization status that is sent back in the response.

See the diagram below for a visual representation of the authorization check:

![Authorization Check Pseudonymization Flow](../images/auth-check.svg)

## Api definitions

For API definitions and specifications, please refer to the Swagger documentation available at `/docs` endpoint of the running application or the `/openapi.json` endpoint for the raw OpenAPI specification.
