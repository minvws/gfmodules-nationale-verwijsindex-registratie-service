# Pseudonymization flows

Pseudonymization is used for the main process in the NVI-RS: referral registration and authorization checks. Their pseudonymization flows are described below.

- [Referral Registration](#referral-registration)

## Referral Registration

The NVI-RS pseudonymizes patient identifiers before registering them as referrals in the NVI.
This process ensures patient privacy and compliance with data protection regulations. The pseudonymization flow involves the following steps:

1. **Register at PRS** - The NVI-RS sends a request to the Pseudoniemendienst (PRS) to register the itself as an organization, after which it registers its certificate. This step is done once during the initial setup and is not needed for each referral registration.
2. **Blind BSN** - The NVI-RS creates a blinded input and blinded factor from the BSN.
3. **Request OPRF-JWE** - The NVI-RS sends the blinded BSN to the PRS and requests an OPRF-JWE.
4. **Register referral** - The NVI-RS sends a create referral request to the NVI.

See the diagram below for a visual representation of the pseudonymization flow during referral registration:

![Referral Registration Pseudonymization Flow](../images/referral-registration-pseudonymization-flow.svg)
