"""
Quantum Encryption Module for QuMail
Implements quantum-inspired encryption using One-Time Pad (OTP)
"""

import os
import secrets
import logging
import hashlib
from typing import Union

logger = logging.getLogger(__name__)

class QuantumEncryption:
    """Quantum-inspired encryption using One-Time Pad"""
    
    def __init__(self, config):
        self.config = config
        self.algorithm = getattr(config, 'ENCRYPTION_ALGORITHM', 'OTP')
        self.default_key_length = getattr(config, 'DEFAULT_KEY_LENGTH', 256)
        logger.info(f"Quantum encryption initialized with {self.algorithm}")
    
    def generate_quantum_key(self, length: int = None) -> bytes:
        """Generate a quantum key using cryptographically secure random"""
        if length is None:
            length = self.default_key_length
        
        # Use secrets for cryptographically secure random generation
        key = secrets.token_bytes(length)
        logger.info(f"Generated quantum key of {length} bytes")
        return key
    
    def encrypt_otp(self, data: bytes, key_id: str) -> bytes:
        """Encrypt data using One-Time Pad with key derivation"""
        try:
            # Derive key from key_id (in real implementation, this would retrieve from key manager)
            derived_key = self._derive_key_from_id(key_id, len(data))
            
            # XOR encryption (One-Time Pad)
            encrypted = bytes(d ^ k for d, k in zip(data, derived_key))
            logger.info(f"Data encrypted with OTP ({len(encrypted)} bytes)")
            return encrypted
            
        except Exception as e:
            logger.error(f"OTP encryption failed: {e}")
            raise
    
    def decrypt_otp(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data using One-Time Pad with key derivation"""
        try:
            # Derive key from key_id
            derived_key = self._derive_key_from_id(key_id, len(encrypted_data))
            
            # XOR decryption (One-Time Pad)
            decrypted = bytes(e ^ k for e, k in zip(encrypted_data, derived_key))
            logger.info(f"Data decrypted with OTP ({len(decrypted)} bytes)")
            return decrypted
            
        except Exception as e:
            logger.error(f"OTP decryption failed: {e}")
            raise
    
    def _derive_key_from_id(self, key_id: str, length: int) -> bytes:
        """Derive encryption key from key ID"""
        # Use PBKDF2 for key derivation (simplified for demo)
        salt = b"qumail_salt_2024"
        key = hashlib.pbkdf2_hmac('sha256', key_id.encode(), salt, 100000, length)
        return key
    
    def encrypt_message(self, message: str, key: bytes) -> bytes:
        """Encrypt message using quantum key"""
        try:
            message_bytes = message.encode('utf-8')
            
            if len(key) < len(message_bytes):
                # Extend key if needed (not ideal for true OTP, but practical)
                extended_key = (key * ((len(message_bytes) // len(key)) + 1))[:len(message_bytes)]
                key = extended_key
            
            encrypted = bytes(m ^ k for m, k in zip(message_bytes, key))
            logger.info(f"Message encrypted successfully ({len(encrypted)} bytes)")
            return encrypted
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_message(self, encrypted_data, key) -> str:
        """Decrypt message using quantum key"""
        try:
            import base64
            
            # Ensure encrypted_data is bytes
            if isinstance(encrypted_data, str):
                try:
                    # Try base64 decode first (most common case)
                    encrypted_data = base64.b64decode(encrypted_data)
                    logger.info("Converted encrypted data from base64 string to bytes")
                except Exception as e:
                    logger.warning(f"Base64 decode failed: {e}, trying UTF-8 encode")
                    encrypted_data = encrypted_data.encode('utf-8')
            
            # Ensure key is bytes
            if isinstance(key, str):
                try:
                    # Try base64 decode first (most common case)
                    key = base64.b64decode(key)
                    logger.info("Converted key from base64 string to bytes")
                except Exception as e:
                    logger.warning(f"Base64 decode of key failed: {e}, trying UTF-8 encode")
                    key = key.encode('utf-8')
            
            if len(key) < len(encrypted_data):
                # Extend key if needed
                extended_key = (key * ((len(encrypted_data) // len(key)) + 1))[:len(encrypted_data)]
                key = extended_key
            
            decrypted_bytes = bytes(e ^ k for e, k in zip(encrypted_data, key))
            message = decrypted_bytes.decode('utf-8')
            logger.info("Message decrypted successfully")
            return message
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def test_encryption(self) -> bool:
        """Test encryption functionality"""
        try:
            # Test with simple data
            test_data = b"Hello, QuMail Quantum Encryption!"
            test_key_id = "test_key_123"
            
            # Encrypt
            encrypted = self.encrypt_otp(test_data, test_key_id)
            
            # Decrypt
            decrypted = self.decrypt_otp(encrypted, test_key_id)
            
            # Verify
            if decrypted == test_data:
                logger.info("Quantum encryption test passed")
                return True
            else:
                logger.error("Quantum encryption test failed: data mismatch")
                return False
                
        except Exception as e:
            logger.error(f"Quantum encryption test failed: {e}")
            return False