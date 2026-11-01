# SecureChat Pro

**CREATED AND POWERED BY DERNOUNI SAMI "CYBER SECURITY EXPERT"**

SecureChat Pro is an encrypted messaging workflow using:

- Terminal chat for CMD / PowerShell
- Desktop encryption/decryption GUI
- AES-256-GCM
- scrypt password-based key derivation
- Random salt and nonce per message
- SC2 message envelope
- Replay protection in automatic mode
- Local simulation and security tests

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![CI](https://github.com/1xsvmi/securechat-pro/actions/workflows/ci.yml/badge.svg)

---

## Project Structure

```text
securechat-pro/
├── chat.py
├── crypt_app.py
├── crypto_core.py
├── simulation.py
├── requirements.txt
├── SECURITY.md
├── SIGNATURE.txt
├── LICENSE
├── .gitignore
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Features

### 1. Terminal transport: `chat.py`

Works in CMD or PowerShell.

Manual mode:

```bash
python chat.py
```

Automatic encrypted mode:

```bash
python chat.py --auto
```

Commands:

```text
/help
/exit
/ips
/status
```

---

### 2. GUI encrypt/decrypt app: `crypt_app.py`

```bash
python crypt_app.py
```

Features:

- Write message
- Encrypt
- Copy encrypted token
- Paste received encrypted token
- Decrypt
- Show token fingerprint
- Show issued/expiry time when available
- Warn about repeated decrypted tokens

On Linux, Tkinter may require:

```bash
sudo apt install python3-tk
```

---

### 3. Security core: `crypto_core.py`

Uses:

- AES-256-GCM
- scrypt: `n=2^15, r=8, p=1`
- 16-byte random salt per message
- 12-byte random nonce per message
- Authenticated Associated Data: `SecureChat-v2`
- SC2 token format
- Optional replay cache
- Optional message expiry via environment variable

---

### 4. Simulation: `simulation.py`

Run local tests without needing another computer:

```bash
python simulation.py
```

It tests:

- Encrypt/decrypt
- Wrong password
- Tampered ciphertext
- Replay detection
- Expired token rejection
- Two-party local loopback messaging

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Usage

### Manual two-window mode

Terminal 1:

```bash
python chat.py
```

Terminal 2:

```bash
python crypt_app.py
```

Workflow:

1. Agree on a password outside the chat.
2. Write message in GUI.
3. Press Encrypt.
4. Copy encrypted text.
5. Paste into `chat.py` and send.
6. Receiver copies encrypted text from `chat.py`.
7. Paste into GUI and decrypt.

---

### Automatic terminal mode

Party A:

```bash
python chat.py --listen --auto
```

Party B:

```bash
python chat.py --connect PARTY_A_IP --auto
```

Both must use the same password.

Local test:

Party A:

```bash
python chat.py --listen --auto
```

Party B:

```bash
python chat.py --connect 127.0.0.1 --auto
```

---

## Optional message expiry

By default, messages do not expire to avoid clock synchronization problems.

To enable 1-hour expiry:

Linux/macOS:

```bash
SECURECHAT_TTL=3600 python chat.py --auto
```

Windows PowerShell:

```powershell
$env:SECURECHAT_TTL="3600"
python chat.py --auto
```

Windows CMD:

```cmd
set SECURECHAT_TTL=3600
python chat.py --auto
```

---

## Network notes

### Same Wi-Fi / LAN

Use the private IPv4 address.

Windows:

```cmd
ipconfig
```

Linux/macOS:

```bash
ip addr
```

or:

```bash
ifconfig
```

### Different networks

Recommended:

- Tailscale
- ZeroTier

These create a private virtual network without router port forwarding.

Windows Firewall may ask for permission. Allow Python for private networks.

---

## Architecture

### Manual mode

```text
User A                         Network                      User B
+----------------+             +--------+             +----------------+
| crypt_app.py   | copy/paste  | chat.py| TCP         | crypt_app.py   |
| GUI encrypt    |-----------> | CLI    |-----------> | GUI decrypt    |
| GUI decrypt    |<----------- |        |<----------- | GUI encrypt    |
+-------+--------+             +---+----+             +-------+--------+
        |                         |                          |
        v                         v                          v
   crypto_core.py <----------------------------------> crypto_core.py
   AES-256-GCM + scrypt + SC2 envelope
```

### Automatic mode

```text
chat.py --auto
   |
   v
crypto_core.py
   |
   v
TCP socket transport
```

---

## Security model

SecureChat Pro encrypts message payloads using AES-256-GCM and a password-derived key. The TCP transport itself is not independently encrypted, and metadata such as IP addresses, ports, timing, and message sizes may still be observable by a network attacker.

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

What is protected:

- Message content
- Message integrity
- Tamper detection
- Password is never sent over the network
- Each message uses fresh salt and nonce
- Replay detection in automatic mode
- Optional expiry

What is not protected by default:

- Metadata: IP addresses, timing, message sizes
- Endpoint compromise
- Weak passwords
- Malicious receiver/sender if password is shared
- Advanced traffic analysis

Use a strong shared password, for example:

```text
correct-horse-battery-staple-2026
```

Do not reuse passwords.

---

## Threat Model

| Threat | Current Protection |
|---|---|
| Content eavesdropping | AES-256-GCM |
| Message tampering | GCM authentication tag |
| Password guessing | scrypt |
| Replay of old messages | ReplayCache in automatic mode |
| Expired messages | Optional TTL via `SECURECHAT_TTL` |
| Protocol injection | Length-prefixed framing |
| Large message DoS | Max message size |
| Password leak over network | Password is never transmitted |
| Version mismatch | SC2 prefix + version field |

---

## Roadmap

Future professional improvements:

1. Merge GUI and terminal into one application.
2. Add X25519 ECDH key exchange.
3. Add forward secrecy.
4. Add double-ratchet-style session keys.
5. Add persistent encrypted message history.
6. Add multi-user rooms.
7. Add packaging as a CLI tool:
   ```bash
   securechat listen --auto
   securechat connect IP --auto
   securechat gui
   securechat simulate
   ```

---

## License

MIT License.

---

## Creator

**CREATED AND POWERED BY DERNOUNI SAMI "CYBER SECURITY EXPERT"**
