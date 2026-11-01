# Security Policy

## Supported Versions

Only the latest version on the `main` branch is supported.

## Reporting A Vulnerability

Please report security vulnerabilities privately.

Do not open a public issue containing exploit details.

If GitHub Private Vulnerability Reporting is enabled, use it.

Otherwise, contact the maintainer through a secure channel.

## Scope

This project focuses on:

- Message confidentiality
- Message integrity
- Password-based encryption
- Replay detection in automatic mode
- Local simulation and testing

It does not claim to protect against:

- Compromised endpoints
- Weak shared passwords
- Traffic analysis
- Metadata leakage
- Malicious participants who already possess the shared password

## Security Boundary

SecureChat Pro encrypts message payloads using AES-256-GCM and a password-derived key. The TCP transport itself is not independently encrypted, and metadata such as IP addresses, ports, timing, and message sizes may still be observable by a network attacker.
