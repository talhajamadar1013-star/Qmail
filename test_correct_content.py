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

print("🔍 TESTING CORRECT ENCRYPTED CONTENT FROM DATABASE")
print("=" * 60)

recipient = 'jauwwad.nallamandu123@gmail.com'
key_id = '82d8e999-4bef-4989-8963-591e797df667'
correct_encrypted_content = 'qHAs16oSkpslsGWjO4Dnebb9vtL4p1IeLtI='  # From database

print(f"Recipient: {recipient}")
print(f"Key ID: {key_id}")
print(f"Correct encrypted content: {correct_encrypted_content}")
print()

# Get the key
user_keys = km.get_user_keys(recipient, include_expired=True)
decryption_key = None

for key in user_keys:
    if key.get('key_id') == key_id:
        decryption_key = key.get('key_data')
        print(f"✅ Found matching key!")
        break

if not decryption_key:
    print("❌ No matching key found!")
    sys.exit(1)

# Ensure key is bytes
if isinstance(decryption_key, str):
    decryption_key = base64.b64decode(decryption_key)

print("\n🔐 ATTEMPTING DECRYPTION WITH CORRECT CONTENT...")
print("-" * 50)

try:
    # Base64 decode the correct encrypted content
    encrypted_bytes = base64.b64decode(correct_encrypted_content)
    print(f"Encrypted bytes: {encrypted_bytes}")
    print(f"Encrypted bytes length: {len(encrypted_bytes)}")
    
    # Decrypt using quantum crypto
    decrypted_message = quantum_crypto.decrypt_message(encrypted_bytes, decryption_key)
    print(f"✅ SUCCESS! Decrypted message: '{decrypted_message}'")
    
except Exception as e:
    print(f"❌ Decryption failed: {e}")

print("\n" + "=" * 60)