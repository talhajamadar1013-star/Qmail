"""
Targeted fix for decrypt_message type error
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config
from qumail_client.embedded_km.neon_key_manager import NeonKeyManager
from qumail_client.crypto.quantum_encryption import QuantumEncryption
import base64

def test_decryption_types():
    print("🔍 TESTING DECRYPTION TYPE ISSUES")
    print("=" * 60)
    
    config = Config()
    key_manager = NeonKeyManager(config)
    quantum_crypto = QuantumEncryption(config)
    
    # Test data from successful case
    recipient_email = "jauwwad.nallamandu123@gmail.com"
    key_id = "82d8e999-4bef-4989-8963-591e797df667"
    correct_encrypted_content = "qHAs16oSkpslsGWjO4Dnebb9vtL4p1IeLtI="
    
    # Get the key (this works)
    user_keys = key_manager.get_user_keys(recipient_email, include_expired=True)
    decryption_key = None
    
    for key in user_keys:
        if key.get('key_id') == key_id:
            decryption_key = key.get('key_data')
            print(f"✅ Found key data type: {type(decryption_key)}")
            break
    
    if not decryption_key:
        print("❌ No key found")
        return
    
    # Test different scenarios that could happen in web interface
    print("\n🧪 TESTING DIFFERENT SCENARIOS")
    print("-" * 50)
    
    # Scenario 1: Both encrypted_content and key are correct types (this should work)
    print("Scenario 1: Correct types (encrypted=bytes, key=bytes)")
    try:
        encrypted_bytes = base64.b64decode(correct_encrypted_content)
        result = quantum_crypto.decrypt_message(encrypted_bytes, decryption_key)
        print(f"  ✅ SUCCESS: '{result}'")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
    
    # Scenario 2: encrypted_content is still a string (this might fail)
    print("\nScenario 2: String encrypted content (encrypted=str, key=bytes)")
    try:
        result = quantum_crypto.decrypt_message(correct_encrypted_content, decryption_key)
        print(f"  ✅ SUCCESS: '{result}'")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
    
    # Scenario 3: Key is base64 string instead of bytes
    print("\nScenario 3: Base64 key (encrypted=bytes, key=str)")
    try:
        encrypted_bytes = base64.b64decode(correct_encrypted_content)
        key_as_base64 = base64.b64encode(decryption_key).decode('utf-8')
        result = quantum_crypto.decrypt_message(encrypted_bytes, key_as_base64)
        print(f"  ✅ SUCCESS: '{result}'")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
    
    # Scenario 4: Both are strings
    print("\nScenario 4: Both strings (encrypted=str, key=str)")
    try:
        key_as_base64 = base64.b64encode(decryption_key).decode('utf-8')
        result = quantum_crypto.decrypt_message(correct_encrypted_content, key_as_base64)
        print(f"  ✅ SUCCESS: '{result}'")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
    
    print("\n🔧 TESTING FIXES")
    print("-" * 50)
    
    # Test the fix from web interface code
    print("Testing web interface conversion logic:")
    try:
        # Simulate web interface logic
        encrypted_content = correct_encrypted_content
        key = decryption_key
        
        # Convert key to bytes if needed (web interface does this)
        if isinstance(key, str):
            try:
                key = base64.b64decode(key)
                print("  Converted key from base64 string to bytes")
            except Exception as e:
                print(f"  Base64 decode of key failed: {e}, trying UTF-8 encode")
                key = key.encode('utf-8')
        
        # Convert encrypted content to bytes (Method 1 from web interface)
        encrypted_bytes = base64.b64decode(encrypted_content) if isinstance(encrypted_content, str) else encrypted_content
        print(f"  Encrypted content type: {type(encrypted_bytes)}")
        print(f"  Key type: {type(key)}")
        
        result = quantum_crypto.decrypt_message(encrypted_bytes, key)
        print(f"  ✅ Web interface logic works: '{result}'")
        
    except Exception as e:
        print(f"  ❌ Web interface logic failed: {e}")
        print(f"     This is the exact error from the web interface!")

if __name__ == "__main__":
    test_decryption_types()