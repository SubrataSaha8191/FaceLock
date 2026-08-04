"""Unit tests for password fallback authentication."""

from Core.authentication.password_fallback import PasswordFallback


def test_hash_and_verify():
    handler = PasswordFallback(iterations=10_000)
    pw_hash = handler.hash_password("SecureP@ss1")
    assert isinstance(pw_hash, bytes)
    assert len(pw_hash) == 48
    assert handler.verify_password("SecureP@ss1", pw_hash) is True


def test_wrong_password():
    handler = PasswordFallback(iterations=10_000)
    pw_hash = handler.hash_password("CorrectPass1")
    assert handler.verify_password("WrongPass1", pw_hash) is False


def test_different_hashes_same_password():
    handler = PasswordFallback(iterations=10_000)
    hash1 = handler.hash_password("SamePass1")
    hash2 = handler.hash_password("SamePass1")
    # Different salts produce different hashes
    assert hash1 != hash2
    assert handler.verify_password("SamePass1", hash1) is True
    assert handler.verify_password("SamePass1", hash2) is True


def test_password_strength():
    assert PasswordFallback.is_strong_password("Abc12345") is True
    assert PasswordFallback.is_strong_password("short") is False
    assert PasswordFallback.is_strong_password("alllower1") is False
    assert PasswordFallback.is_strong_password("ALLUPPER1") is False
    assert PasswordFallback.is_strong_password("NoDigits!") is False


def test_invalid_stored_hash():
    handler = PasswordFallback(iterations=10_000)
    assert handler.verify_password("anything", b"short") is False
