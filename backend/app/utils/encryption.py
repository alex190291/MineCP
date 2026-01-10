"""
Encryption utilities for sensitive data storage.
"""
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def get_encryption_key() -> bytes:
    """
    Get the encryption key from configuration.

    Returns:
        Encryption key as bytes

    Raises:
        RuntimeError: If encryption key is not configured
    """
    key = current_app.config.get('ENCRYPTION_KEY')

    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY not configured. Please set the ENCRYPTION_KEY environment variable.\n"
            "Generate a key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )

    # Ensure key is bytes
    if isinstance(key, str):
        key = key.encode('utf-8')

    return key


def encrypt_value(plaintext: str) -> Optional[str]:
    """
    Encrypt a plaintext value.

    Args:
        plaintext: The plaintext string to encrypt

    Returns:
        Encrypted value as string, or None if plaintext is None/empty
    """
    if not plaintext:
        return None

    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(plaintext.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        current_app.logger.error(f"Encryption failed: {e}")
        raise


def decrypt_value(encrypted: str) -> Optional[str]:
    """
    Decrypt an encrypted value.

    Args:
        encrypted: The encrypted string to decrypt

    Returns:
        Decrypted plaintext, or None if encrypted is None/empty

    Raises:
        ValueError: If decryption fails (invalid key or corrupted data)
    """
    if not encrypted:
        return None

    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted.encode('utf-8'))
        return decrypted.decode('utf-8')
    except InvalidToken:
        raise ValueError("Decryption failed: Invalid encryption key or corrupted data")
    except Exception as e:
        current_app.logger.error(f"Decryption failed: {e}")
        raise


def generate_encryption_key() -> str:
    """
    Generate a new encryption key.

    Returns:
        Base64-encoded encryption key as string
    """
    return Fernet.generate_key().decode('utf-8')
