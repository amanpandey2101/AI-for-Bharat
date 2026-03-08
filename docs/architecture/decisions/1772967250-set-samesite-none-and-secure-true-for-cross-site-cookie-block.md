# Set SameSite=none and Secure=True for cross-site cookie block

**Status:** Validated
**Date:** 2026-03-08

## Description
The decision was made to set SameSite=none and Secure=True for cross-site cookie block to prevent cross-site request forgery (CSRF) attacks. This was done by modifying the cookie settings in the application to include SameSite=none and Secure=True. This change will ensure that cookies are only sent over HTTPS and will not be sent in cross-site requests.

## Rationale
The decision was made to prevent CSRF attacks and ensure the security of the application. Setting SameSite=none and Secure=True will prevent attackers from forging requests to the application and stealing user data.

## Alternatives Considered
- Setting SameSite=strict
- Not setting SameSite at all
