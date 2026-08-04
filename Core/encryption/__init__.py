"""Encryption module for biometric templates."""

from Core.encryption.key_manager import KeyManager
from Core.encryption.embedding_encryptor import EmbeddingEncryptor

__all__ = ["KeyManager", "EmbeddingEncryptor"]
