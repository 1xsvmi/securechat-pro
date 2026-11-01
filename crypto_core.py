"""
SecureChat Pro - Crypto Core
AES-256-GCM + scrypt + SC2 message envelope
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from collections import deque

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


PREFIX = "SC2:"
VERSION = 2
AAD = b"SecureChat-v2"

SALT_LEN = 16
NONCE_LEN = 12
TAG_LEN = 16

MAX_RAW_LEN = 1_000_000


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


# By default, messages do not expire to avoid clock synchronization problems.
# Enable with: SECURECHAT_TTL=3600
DEFAULT_TTL = _int_env("SECURECHAT_TTL", 0)

# Allowed clock skew in seconds when checking expiry.
CLOCK_SKEW = _int_env("SECURECHAT_CLOCK_SKEW", 300)


class CryptoError(Exception):
    """Generic crypto layer error."""
    pass


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def _b64decode(text: str) -> bytes:
    text = "".join(text.split())
    missing = len(text) % 4
    if missing:
        text += "=" * (4 - missing)
    return base64.urlsafe_b64decode(text.encode("ascii"))


def derive_key(password: str, salt: bytes) -> bytes:
    if not password:
        raise CryptoError("Password is empty")

    if len(password) > 1024:
        raise CryptoError("Password is too long")

    return Scrypt(
        salt=salt,
        length=32,
        n=2 ** 15,
        r=8,
        p=1,
    ).derive(password.encode("utf-8"))


def encrypt(password: str, message: str, ttl: int | None = None) -> str:
    """
    Encrypt a text message and return an SC2 token.
    """
    if not isinstance(message, str):
        raise CryptoError("Message must be text")

    now = int(time.time())

    if ttl is None:
        ttl = DEFAULT_TTL

    payload = {
        "v": VERSION,
        "iat": now,
        "m": message,
    }

    if ttl != 0:
        payload["exp"] = now + int(ttl)

    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)

    key = derive_key(password, salt)

    plaintext = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    ciphertext = AESGCM(key).encrypt(nonce, plaintext, AAD)

    return PREFIX + _b64encode(salt + nonce + ciphertext)


def decrypt_details(password: str, token: str, verify_expiry: bool = True) -> dict:
    """
    Decrypt an SC2 token and return message details.
    """
    token = (token or "").strip()

    if not token.startswith(PREFIX):
        raise CryptoError("Token is not in SecureChat SC2 format")

    try:
        raw = _b64decode(token[len(PREFIX):])
    except Exception as exc:
        raise CryptoError("Invalid or corrupted encrypted token") from exc

    if len(raw) < SALT_LEN + NONCE_LEN + TAG_LEN:
        raise CryptoError("Encrypted token is too short")

    if len(raw) > MAX_RAW_LEN:
        raise CryptoError("Encrypted token is too large")

    salt = raw[:SALT_LEN]
    nonce = raw[SALT_LEN:SALT_LEN + NONCE_LEN]
    ciphertext = raw[SALT_LEN + NONCE_LEN:]

    try:
        key = derive_key(password, salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, AAD)
    except InvalidTag as exc:
        raise CryptoError("Wrong password or message has been tampered with") from exc
    except CryptoError:
        raise
    except Exception as exc:
        raise CryptoError("Decryption failed") from exc

    try:
        payload = json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        raise CryptoError("Invalid internal payload") from exc

    if not isinstance(payload, dict):
        raise CryptoError("Invalid message structure")

    if payload.get("v") != VERSION:
        raise CryptoError("Unsupported message version")

    message = payload.get("m")
    if not isinstance(message, str):
        raise CryptoError("No valid message inside payload")

    issued_at = payload.get("iat")
    expires_at = payload.get("exp")

    if verify_expiry and expires_at is not None:
        try:
            exp = int(expires_at)
        except Exception as exc:
            raise CryptoError("Invalid expiry time") from exc

        now = int(time.time())

        if now > exp + CLOCK_SKEW:
            raise CryptoError("This message has expired")

    return {
        "message": message,
        "version": payload.get("v"),
        "issued_at": issued_at,
        "expires_at": expires_at,
    }


def decrypt(password: str, token: str, verify_expiry: bool = True) -> str:
    """
    Decrypt an SC2 token and return only the message text.
    """
    return decrypt_details(password, token, verify_expiry=verify_expiry)["message"]


def token_hash(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def token_fingerprint(token: str) -> str:
    return token_hash(token)[:12]


class ReplayCache:
    """
    Bounded cache to detect repeated encrypted tokens.
    Useful in automatic mode: python chat.py --auto
    """

    def __init__(self, max_items: int = 10000):
        self.max_items = max_items
        self.seen = set()
        self.order = deque()

    def check_and_add(self, token: str) -> None:
        fp = token_hash(token)

        if fp in self.seen:
            raise CryptoError("Replay detected: same encrypted token was already received")

        self.seen.add(fp)
        self.order.append(fp)

        if len(self.order) > self.max_items:
            old = self.order.popleft()
            self.seen.discard(old)
