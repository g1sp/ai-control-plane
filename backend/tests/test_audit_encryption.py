"""Tests for AES-256-GCM audit field encryption."""

import base64
import os
import secrets

import pytest

from src.services.audit_encryption import (
    decrypt_field,
    encrypt_field,
    generate_key_b64,
    is_encrypted,
    rekey_value,
)

_ENC_PREFIX = "enc_v1:"


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    key = base64.b64encode(secrets.token_bytes(32)).decode()
    monkeypatch.setenv("AUDIT_ENCRYPTION_KEY", key)
    return key


def test_encrypt_produces_prefix():
    result = encrypt_field("sensitive prompt text")
    assert result.startswith(_ENC_PREFIX)


def test_encrypt_decrypt_roundtrip():
    plaintext = "My credit card is 4111-1111-1111-1111"
    encrypted = encrypt_field(plaintext)
    assert encrypted != plaintext
    assert decrypt_field(encrypted) == plaintext


def test_each_encryption_is_unique():
    p = "same plaintext"
    e1 = encrypt_field(p)
    e2 = encrypt_field(p)
    assert e1 != e2  # unique nonce each time


def test_decrypt_plaintext_passthrough():
    """Plaintext values (no prefix) are returned as-is — backward compat."""
    assert decrypt_field("legacy plaintext") == "legacy plaintext"


def test_decrypt_empty_returns_empty():
    assert decrypt_field("") == ""


def test_is_encrypted_true_for_encrypted():
    enc = encrypt_field("hello")
    assert is_encrypted(enc) is True


def test_is_encrypted_false_for_plaintext():
    assert is_encrypted("just a plain string") is False


def test_tampered_ciphertext_returns_failure():
    enc = encrypt_field("original")
    # Flip a byte in the payload
    prefix, payload = enc[len(_ENC_PREFIX):], enc[:len(_ENC_PREFIX)]
    raw = bytearray(base64.b64decode(prefix))
    raw[-1] ^= 0xFF
    tampered = _ENC_PREFIX + base64.b64encode(bytes(raw)).decode()
    result = decrypt_field(tampered)
    assert result == "[decryption_failed]"


def test_no_key_configured_returns_masked(monkeypatch):
    monkeypatch.delenv("AUDIT_ENCRYPTION_KEY", raising=False)
    enc = _ENC_PREFIX + base64.b64encode(b"fake_payload").decode()
    result = decrypt_field(enc)
    assert result == "[encrypted]"


def test_no_key_encrypt_returns_plaintext(monkeypatch):
    """When no key is set, encrypt_field degrades gracefully (returns plaintext)."""
    monkeypatch.delenv("AUDIT_ENCRYPTION_KEY", raising=False)
    result = encrypt_field("some text")
    assert result == "some text"


def test_generate_key_is_32_bytes():
    key_b64 = generate_key_b64()
    assert len(base64.b64decode(key_b64)) == 32


def test_rekey_roundtrip():
    old_key = generate_key_b64()
    new_key = generate_key_b64()

    plaintext = "secret agent data"
    os.environ["AUDIT_ENCRYPTION_KEY"] = old_key
    encrypted_old = encrypt_field(plaintext)

    rekeyed = rekey_value(encrypted_old, old_key, new_key)
    assert rekeyed != encrypted_old

    os.environ["AUDIT_ENCRYPTION_KEY"] = new_key
    decrypted = decrypt_field(rekeyed)
    assert decrypted == plaintext


def test_rekey_plaintext_value():
    """Plaintext values get encrypted with new key during rekey."""
    old_key = generate_key_b64()
    new_key = generate_key_b64()
    rekeyed = rekey_value("raw plaintext", old_key, new_key)
    assert rekeyed.startswith(_ENC_PREFIX)
    os.environ["AUDIT_ENCRYPTION_KEY"] = new_key
    assert decrypt_field(rekeyed) == "raw plaintext"
