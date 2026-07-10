# Security Policy

## Secrets

This repository must never contain:

- Snowflake passwords
- RSA private keys
- RSA public keys used by a real account
- `profile.json`
- account-specific URLs or identifiers
- production user names
- access tokens

Use `profile.example.json` only as a template.

## Reporting

Report suspected credential exposure privately to the repository owner. Do not open a public issue containing credentials or key material.

## Key rotation

When a private key may have been exposed:

1. Generate a new key pair.
2. Register the new public key as `RSA_PUBLIC_KEY_2`.
3. Validate authentication with the new private key.
4. Remove or replace the old public key.
5. Revoke any compromised credentials.
