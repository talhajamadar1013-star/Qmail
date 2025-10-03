#!/usr/bin/env python3
"""
QuMail Key Manager API Test Script
Tests the REST API endpoints for quantum key management
"""

import requests
import json
import sys
import hashlib
from typing import Dict, Any

class KeyManagerAPIClient:
    """Client for testing Key Manager API"""
    
    def __init__(self, base_url: str = "http://localhost:5000", api_token: str = "test_token"):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.user_id = "test_user@example.com"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}',
            'X-User-ID': self.user_id
        }
    
    def test_generate_key(self, key_length: int = 256) -> Dict[str, Any]:
        """
        Test POST /keys - Generate new key
        """
        print(f"🔑 Testing key generation...")
        
        url = f"{self.base_url}/keys"
        payload = {
            "key_length": key_length,
            "user_id": self.user_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 201:
                print("✅ Key generation successful!")
                return result
            else:
                print("❌ Key generation failed!")
                return {}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def test_fetch_key(self, key_id: str) -> Dict[str, Any]:
        """
        Test GET /keys/<key_id> - Fetch key for client
        """
        print(f"📥 Testing key fetch for {key_id}...")
        
        url = f"{self.base_url}/keys/{key_id}"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            
            # Don't print the actual key bytes for security
            safe_result = {k: v if k != 'key_bytes' else f"<{len(v)} hex chars>" 
                          for k, v in result.items()}
            print(f"Response: {json.dumps(safe_result, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Key fetch successful!")
                return result
            else:
                print("❌ Key fetch failed!")
                return {}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def test_mark_key_used(self, key_id: str) -> Dict[str, Any]:
        """
        Test PATCH /keys/<key_id>/use - Mark key as used
        """
        print(f"✏️  Testing mark key as used for {key_id}...")
        
        url = f"{self.base_url}/keys/{key_id}/use"
        
        try:
            response = requests.patch(url, headers=self._get_headers())
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Key marked as used successfully!")
                return result
            else:
                print("❌ Mark key as used failed!")
                return {}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def test_fetch_key_hash(self, key_id: str) -> Dict[str, Any]:
        """
        Test GET /keys/<key_id>/hash - Fetch key hash for verification
        """
        print(f"🔍 Testing key hash fetch for {key_id}...")
        
        url = f"{self.base_url}/keys/{key_id}/hash"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Key hash fetch successful!")
                return result
            else:
                print("❌ Key hash fetch failed!")
                return {}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def test_health_check(self) -> bool:
        """Test health endpoint"""
        print(f"❤️  Testing health check...")
        
        url = f"{self.base_url}/health"
        
        try:
            response = requests.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Service: {result.get('service', 'Unknown')}")
                print(f"Version: {result.get('version', 'Unknown')}")
                print("✅ Health check passed!")
                return True
            else:
                print("❌ Health check failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 QuMail Key Manager API Test Suite")
        print("=" * 50)
        
        # Test 1: Health check
        print("\n1️⃣  Health Check")
        print("-" * 30)
        if not self.test_health_check():
            print("❌ API server is not responding. Please start the server first.")
            return
        
        # Test 2: Generate key
        print("\n2️⃣  Generate Key")
        print("-" * 30)
        key_data = self.test_generate_key(256)
        if not key_data:
            print("❌ Cannot continue without a key.")
            return
        
        key_id = key_data.get('key_id')
        print(f"Generated Key ID: {key_id}")
        
        # Test 3: Fetch key
        print("\n3️⃣  Fetch Key")
        print("-" * 30)
        fetched_key = self.test_fetch_key(key_id)
        
        # Test 4: Fetch key hash
        print("\n4️⃣  Fetch Key Hash")
        print("-" * 30)
        key_hash = self.test_fetch_key_hash(key_id)
        
        # Verify hash consistency (if we have the key bytes)
        if fetched_key.get('key_bytes') and key_hash.get('hash'):
            expected_hash = hashlib.sha256(bytes.fromhex(fetched_key['key_bytes'])).hexdigest()
            actual_hash = key_hash['hash']
            
            if expected_hash == actual_hash:
                print("✅ Hash verification successful!")
            else:
                print("❌ Hash verification failed!")
                print(f"Expected: {expected_hash}")
                print(f"Actual: {actual_hash}")
        
        # Test 5: Mark key as used
        print("\n5️⃣  Mark Key as Used")
        print("-" * 30)
        used_result = self.test_mark_key_used(key_id)
        
        # Test 6: Try to fetch used key (should fail)
        print("\n6️⃣  Fetch Used Key (Should Fail)")
        print("-" * 30)
        self.test_fetch_key(key_id)
        
        print(f"\n🎉 Test suite completed!")
        print(f"API Base URL: {self.base_url}")
        print(f"User ID: {self.user_id}")

def main():
    """Main test function"""
    
    # Parse command line arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    api_token = sys.argv[2] if len(sys.argv) > 2 else "test_token_123"
    
    print(f"Testing API at: {base_url}")
    print(f"Using API token: {api_token}")
    
    # Create API client and run tests
    client = KeyManagerAPIClient(base_url, api_token)
    client.run_full_test_suite()

if __name__ == "__main__":
    main()