#!/usr/bin/env python3
import os, sys
sys.path.insert(0, '.')
from qumail_client.embedded_km.neon_key_manager import NeonKeyManager
from qumail_client.crypto.quantum_encryption import QuantumEncryption
from config.settings import load_config
import base64

config = load_config()
km = NeonKeyManager(config)
quantum_crypto = QuantumEncryption(config)

print("🧪 COMPREHENSIVE ENCRYPTION/DECRYPTION TEST")
print("=" * 60)

# Test 1: Basic encryption/decryption with same key
print("\n1. Testing basic encryption/decryption...")
test_message = "Hello, this is a test message!"
test_key = km.generate_quantum_key(
    user_id='test@example.com',
    recipient='test2@example.com',
    purpose='debug_test'
)

print(f"Original message: '{test_message}'")
encrypted = quantum_crypto.encrypt_message(test_message, test_key['key_data'])
print(f"Encrypted bytes: {encrypted}")
print(f"Encrypted base64: {base64.b64encode(encrypted).decode()}")

decrypted = quantum_crypto.decrypt_message(encrypted, test_key['key_data'])
print(f"Decrypted message: '{decrypted}'")
print(f"Match: {'✅ YES' if test_message == decrypted else '❌ NO'}")

# Clean up test key
km.delete_key(test_key['key_id'], 'test@example.com')

print("\n" + "-" * 60)

# Test 2: Try to decrypt the actual problematic message
print("\n2. Testing the actual problematic message...")
recipient = 'jauwwad.nallamandu123@gmail.com'
key_id = '82d8e999-4bef-4989-8963-591e797df667'
encrypted_content = 'q3+5dEeay2/Jfgsf2QN5hTG8vPQARfzoFxPsmg=='

# Get the key
user_keys = km.get_user_keys(recipient, include_expired=True)
actual_key = None
for key in user_keys:
    if key.get('key_id') == key_id:
        actual_key = key.get('key_data')
        break

if actual_key:
    print(f"Key found: {len(actual_key)} bytes")
    
    # Try base64 decode of encrypted content
    try:
        encrypted_bytes = base64.b64decode(encrypted_content)
        print(f"Encrypted bytes: {encrypted_bytes}")
        print(f"Encrypted bytes length: {len(encrypted_bytes)}")
        
        # Check if key length matches
        if len(actual_key) < len(encrypted_bytes):
            extended_key = (actual_key * ((len(encrypted_bytes) // len(actual_key)) + 1))[:len(encrypted_bytes)]
            print(f"Extended key length: {len(extended_key)}")
        else:
            extended_key = actual_key[:len(encrypted_bytes)]
            print(f"Truncated key length: {len(extended_key)}")
        
        # Manual XOR decryption
        decrypted_bytes = bytes(e ^ k for e, k in zip(encrypted_bytes, extended_key))
        print(f"Raw decrypted bytes: {decrypted_bytes}")
        print(f"Raw decrypted hex: {decrypted_bytes.hex()}")
        
        # Try different decodings
        encodings = ['utf-8', 'latin1', 'ascii', 'utf-16']
        for encoding in encodings:
            try:
                decoded = decrypted_bytes.decode(encoding)
                print(f"Decoded with {encoding}: '{decoded}'")
                if decoded.isprintable():
                    print(f"✅ SUCCESS with {encoding}: '{decoded}'")
                    break
            except Exception as e:
                print(f"Failed with {encoding}: {e}")
                
    except Exception as e:
        print(f"Base64 decode failed: {e}")
else:
    print("❌ Key not found!")

print("\n" + "=" * 60)