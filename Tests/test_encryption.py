"""Unit tests for key manager and vector encryption."""

import pytest
import numpy as np

from Core.utils.crypto_utils import derive_key, generate_salt
from Core.encryption.key_manager import KeyManager
from Core.encryption.embedding_encryptor import EmbeddingEncryptor


def test_key_derivation():
    salt = generate_salt(16)
    assert len(salt) == 16
    key1 = derive_key("secret123", salt)
    key2 = derive_key("secret123", salt)
    assert key1 == key2
    assert len(key1) == 32


def test_key_manager():
    km = KeyManager("mysecret")
    assert len(km.get_key()) == 32
    assert len(km.get_salt()) == 16


def test_vector_encryption_decryption():
    km = KeyManager("strong_passphrase")
    encryptor = EmbeddingEncryptor(km.get_key())

    # Create dummy 128-dim vector
    original_vec = np.random.rand(128).astype(np.float32)
    encrypted_payload = encryptor.encrypt_vector(original_vec)

    assert isinstance(encrypted_payload, bytes)
    assert len(encrypted_payload) > 12

    decrypted_vec = encryptor.decrypt_vector(encrypted_payload)
    assert np.allclose(original_vec, decrypted_vec, atol=1e-5)


def test_invalid_key_length():
    with pytest.raises(ValueError):
        EmbeddingEncryptor(b"short_key")
