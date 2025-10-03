"""
Debug key format differences between test script and web interface
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config
from qumail_client.embedded_km.neon_key_manager import NeonKeyManager
import base64

def debug_key_format():
    print("🔍 DEBUGGING KEY FORMAT DIFFERENCES")
    print("=" * 60)
    
    config = Config()
    key_manager = NeonKeyManager(config)
    
    # Test data
    recipient_email = "jauwwad.nallamandu123@gmail.com"
    key_id = "82d8e999-4bef-4989-8963-591e797df667"
    
    # Get keys using the method from test script (works)
    print("📋 METHOD 1: Test script method (get_user_keys with email)")
    print("-" * 50)
    user_keys_by_email = key_manager.get_user_keys(recipient_email, include_expired=True)
    key_data_raw = None
    
    print(f"Found {len(user_keys_by_email)} keys for email {recipient_email}")
    for key in user_keys_by_email:
        if key.get('key_id') == key_id:
            key_data_raw = key.get('key_data')
            print(f"✅ Found matching key!")
            print(f"✅ Raw key data type: {type(key_data_raw)}")
            print(f"✅ Raw key data length: {len(key_data_raw) if key_data_raw else 0}")
            if key_data_raw:
                print(f"✅ Raw key data preview: {str(key_data_raw)[:50]}...")
            
            if isinstance(key_data_raw, str):
                try:
                    decoded_key = base64.b64decode(key_data_raw)
                    print(f"✅ Base64 decoded type: {type(decoded_key)}")
                    print(f"✅ Base64 decoded length: {len(decoded_key)}")
                except Exception as e:
                    print(f"❌ Base64 decode failed: {e}")
            break
    
    if not key_data_raw:
        print("❌ No key found with test script method")
    
    print("\n📋 METHOD 2: Web interface method (get_user_keys)")
    print("-" * 50)
    
    # Get user ID first
    user_id = key_manager.get_user_id_by_email(recipient_email)
    print(f"User ID: {user_id}")
    
    if user_id:
        user_keys = key_manager.get_user_keys(user_id, include_expired=True)
        print(f"Found {len(user_keys)} keys for user")
        
        for i, key in enumerate(user_keys):
            print(f"\nKey {i+1}:")
            print(f"  Key ID: {key.get('key_id')}")
            print(f"  Purpose: {key.get('purpose')}")
            print(f"  Key data type: {type(key.get('key_data'))}")
            if key.get('key_data'):
                print(f"  Key data length: {len(key.get('key_data'))}")
                print(f"  Key data preview: {str(key.get('key_data'))[:50]}...")
            
            if key.get('key_id') == key_id:
                print(f"  🎯 THIS IS THE MATCHING KEY!")
                key_data_web = key.get('key_data')
                
                # Test different conversion approaches
                print(f"\n  🧪 Testing conversions:")
                
                # Test 1: Direct use (if already bytes)
                if isinstance(key_data_web, bytes):
                    print(f"    ✅ Already bytes: {len(key_data_web)} bytes")
                else:
                    print(f"    ❌ Not bytes: {type(key_data_web)}")
                
                # Test 2: Base64 decode
                if isinstance(key_data_web, str):
                    try:
                        decoded = base64.b64decode(key_data_web)
                        print(f"    ✅ Base64 decode success: {len(decoded)} bytes")
                        
                        # Compare with raw key
                        if key_data_raw and isinstance(key_data_raw, str):
                            raw_decoded = base64.b64decode(key_data_raw)
                            if decoded == raw_decoded:
                                print(f"    ✅ MATCHES raw key data!")
                            else:
                                print(f"    ❌ DIFFERENT from raw key data")
                                print(f"       Web decoded: {decoded[:20]}...")
                                print(f"       Raw decoded: {raw_decoded[:20]}...")
                        
                    except Exception as e:
                        print(f"    ❌ Base64 decode failed: {e}")
                
                # Test 3: UTF-8 encode
                if isinstance(key_data_web, str):
                    try:
                        encoded = key_data_web.encode('utf-8')
                        print(f"    ✅ UTF-8 encode: {len(encoded)} bytes")
                    except Exception as e:
                        print(f"    ❌ UTF-8 encode failed: {e}")
    else:
        print("❌ No user ID found")

if __name__ == "__main__":
    debug_key_format()