# -*- coding: utf-8 -*-
"""
AES对称加密，GCM模式
"""
import abc
import base64
import os
from binascii import a2b_hex, b2a_hex

from blue_krill.encoding import force_bytes, force_text
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VALID_AES128_KEY_SIZE = 16
VALID_AES256_KEY_SIZE = 32
MODE_GCM_NONCE_SIZE = 12
MODE_GCM_MAC_LEN = 16


class AbstractCipher(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def encrypt_to_hex(self, plaintext: str) -> str:
        """加密"""

    @abc.abstractmethod
    def decrypt_from_hex(self, encrypted_text: str) -> str:
        """解密"""


class AESGCMCipher(AbstractCipher):
    def __init__(self, key: bytes, nonce: bytes = b""):
        key = base64.b64decode(key)

        if len(key) not in (VALID_AES128_KEY_SIZE, VALID_AES256_KEY_SIZE):
            raise ValueError("invalid key, length should be 16 or 32")

        if nonce and len(nonce) != MODE_GCM_NONCE_SIZE:
            raise ValueError("invalid nonce, length should be 12")

        # It must be 16, 32 bytes long (respectively for *AES-128*, or *AES-256*)
        self.key = key
        self.nonce = nonce

    def _encrypt(self, plaintext: bytes, nonce: bytes) -> bytes:
        aes_gcm = AESGCM(self.key)
        return aes_gcm.encrypt(nonce, plaintext, None)

    def _decrypt(self, encrypted_text: bytes, nonce: bytes) -> bytes:
        aes_gcm = AESGCM(self.key)
        return aes_gcm.decrypt(nonce, encrypted_text, None)

    def encrypt_to_hex(self, plaintext: str) -> str:
        encrypted_text = self._encrypt(force_bytes(plaintext), self.nonce)
        return force_text(b2a_hex(encrypted_text))

    def decrypt_from_hex(self, encrypted_text: str) -> str:
        unhex_encrypted_text = a2b_hex(encrypted_text)
        return force_text(self._decrypt(unhex_encrypted_text, self.nonce))

    def encrypt_with_random_nonce_to_base64(self, plaintext: str) -> str:
        nonce = os.urandom(MODE_GCM_NONCE_SIZE)
        encrypted_text = self._encrypt(force_bytes(plaintext), nonce)
        return force_text(base64.b64encode(nonce + encrypted_text))

    def decrypt_with_random_nonce_from_base64(self, encrypted_text: str) -> str:
        decoded_encrypted_text = base64.b64decode(force_bytes(encrypted_text))
        nonce = decoded_encrypted_text[:MODE_GCM_NONCE_SIZE]
        ciphertext = decoded_encrypted_text[MODE_GCM_NONCE_SIZE:]
        return force_text(self._decrypt(ciphertext, nonce))


def encrypt_with_random_nonce_to_base64(s: str, key: bytes) -> str:
    """Shortcut function: encrypt a string with AES GCM mode"""
    cipher = AESGCMCipher(key)
    return cipher.encrypt_with_random_nonce_to_base64(s)


def decrypt_with_random_nonce_from_base64(s: str, key: bytes) -> str:
    """Shortcut function: decrypt a string with AES GCM mode"""
    if not s:
        return ""

    cipher = AESGCMCipher(key)
    return cipher.decrypt_with_random_nonce_from_base64(s)
