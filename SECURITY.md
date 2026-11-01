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

## Important Security Boundary

SecureChat Pro encrypts message payloads, not the entire network transport.

The TCP connection used by `chat.py` is a plain socket transport. AES-256-GCM protects the message contents in automatic/manual encrypted workflows, but it does not hide:

- source and destination IP addresses
- port numbers
- connection timing
- message sizes
- the fact that SecureChat SC2 tokens are being exchanged

This project is not a VPN, not Tor, and not a metadata-hiding transport.

For stronger transport security in future versions, add TLS mutual authentication or an ECDH-based encrypted session layer.
