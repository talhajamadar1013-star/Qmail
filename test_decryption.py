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

# Test decryption with the actual encrypted message
recipient = 'jauwwad.nallamandu123@gmail.com'
key_id = '82d8e999-4bef-4989-8963-591e797df667'
encrypted_content = 'q3+5dEeay2/Jfgsf2QN5hTG8vPQARfzoFxPsmg=='

print("🔍 DECRYPTION TEST")
print("=" * 50)
print(f"Recipient: {recipient}")
print(f"Key ID: {key_id}")
print(f"Encrypted content: {encrypted_content}")
print()

# Get the key for the recipient
user_keys = km.get_user_keys(recipient, include_expired=True)
decryption_key = None

print(f"Available keys for {recipient}: {len(user_keys)}")
for key in user_keys:
    print(f"  - Key ID: {key.get('key_id')}")
    if key.get('key_id') == key_id:
        decryption_key = key.get('key_data')
        print(f"  ✅ Found matching key!")
        break

if not decryption_key:
    print("❌ No matching key found!")
    sys.exit(1)

print(f"Key data type: {type(decryption_key)}")
print(f"Key data length: {len(decryption_key) if decryption_key else 0}")

# Ensure key is bytes
if isinstance(decryption_key, str):
    try:
        decryption_key = base64.b64decode(decryption_key)
        print("✅ Converted key from base64 to bytes")
    except:
        decryption_key = decryption_key.encode('utf-8')
        print("✅ Converted key from string to bytes")

print("\n🔐 ATTEMPTING DECRYPTION...")
print("-" * 30)

# Try multiple decryption methods
methods = [
    ("Base64 decode + decrypt", lambda: quantum_crypto.decrypt_message(base64.b64decode(encrypted_content), decryption_key)),
    ("Direct decrypt", lambda: quantum_crypto.decrypt_message(encrypted_content.encode('utf-8'), decryption_key)),
    ("Hex decode + decrypt", lambda: quantum_crypto.decrypt_message(bytes.fromhex(encrypted_content), decryption_key))
]

for method_name, method in methods:
    try:
        print(f"Trying: {method_name}")
        decrypted = method()
        if isinstance(decrypted, bytes):
            decrypted = decrypted.decode('utf-8')
        print(f"✅ SUCCESS! Decrypted message: '{decrypted}'")
        break
    except Exception as e:
        print(f"❌ Failed: {e}")

print("\n" + "=" * 50)