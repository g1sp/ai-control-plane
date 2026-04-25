"""
AES-256-GCM encryption for audit log sensitive fields.

Key is derived from AUDIT_ENCRYPTION_KEY env var (base64-encoded 32 bytes).
Encrypted values are stored as: enc_v1:<base64(nonce + ciphertext + tag)>
The enc_v1: prefix makes encrypted vs plaintext fields detectable at read time.

GCM chosen over CBC: authenticated encryption detects tampering in addition to
providing confidentiality. Each record gets a unique random 12-byte nonce.
"""

import base64
import logging
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

_PREFIX = "enc_v1:"
_NONCE_BYTES = 12


def _load_key() -> bytes | None:
    from ..config import settings
    raw = settings.audit_encryption_key.strip() or os.environ.get("AUDIT_ENCRYPTION_KEY", "").strip()
    if not raw:
        return None
    try:
        key = base64.b64decode(raw)
        if len(key) != 32:
            logger.error("AUDIT_ENCRYPTION_KEY must decode to exactly 32 bytes, got %d", len(key))
            return None
        return key
    except Exception as e:
        logger.error("Failed to decode AUDIT_ENCRYPTION_KEY: %s", e)
        return None


def encrypt_field(plaintext: str) -> str:
    """
    Encrypt a string field for storage. Returns enc_v1:<base64> or plaintext
    if no key is configured (graceful degradation — encryption is optional).
    """
    key = _load_key()
    if key is None:
        return plaintext

    nonce = secrets.token_bytes(_NONCE_BYTES)
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext.encode(), None)
    payload = base64.b64encode(nonce + ciphertext_with_tag).decode()
    return f"{_PREFIX}{payload}"


def decrypt_field(value: str) -> str:
    """
    Decrypt a field value. Handles both encrypted (enc_v1: prefix) and
    plaintext values transparently so reads work during key rotation periods.
    """
    if not value or not value.startswith(_PREFIX):
        return value

    key = _load_key()
    if key is None:
        logger.warning("Encrypted field found but AUDIT_ENCRYPTION_KEY not set — returning masked value")
        return "[encrypted]"

    try:
        payload = base64.b64decode(value[len(_PREFIX):])
        nonce = payload[:_NONCE_BYTES]
        ciphertext_with_tag = payload[_NONCE_BYTES:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext_with_tag, None).decode()
    except Exception as e:
        logger.error("Failed to decrypt audit field: %s", e)
        return "[decryption_failed]"


def is_encrypted(value: str) -> bool:
    return bool(value and value.startswith(_PREFIX))


def rekey_value(value: str, old_key_b64: str, new_key_b64: str) -> str:
    """
    Re-encrypt a single value with a new key. Used by the rekey endpoint.
    Handles plaintext values (encrypts them with new key).
    """
    old_key = base64.b64decode(old_key_b64)
    new_key = base64.b64decode(new_key_b64)

    if len(old_key) != 32 or len(new_key) != 32:
        raise ValueError("Both keys must be 32 bytes")

    # Decrypt with old key
    if value.startswith(_PREFIX):
        payload = base64.b64decode(value[len(_PREFIX):])
        nonce = payload[:_NONCE_BYTES]
        ct = payload[_NONCE_BYTES:]
        plaintext = AESGCM(old_key).decrypt(nonce, ct, None).decode()
    else:
        plaintext = value

    # Re-encrypt with new key
    new_nonce = secrets.token_bytes(_NONCE_BYTES)
    new_ct = AESGCM(new_key).encrypt(new_nonce, plaintext.encode(), None)
    payload = base64.b64encode(new_nonce + new_ct).decode()
    return f"{_PREFIX}{payload}"


def generate_key_b64() -> str:
    """Generate a new random 32-byte key, base64-encoded. For key setup/rotation."""
    return base64.b64encode(secrets.token_bytes(32)).decode()
