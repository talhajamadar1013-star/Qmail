#!/usr/bin/env python3
"""
Test script for QuMail Flask application
"""

import requests
import json

# Base URL for the Flask app
BASE_URL = "http://127.0.0.1:5000"

def test_login():
    """Test login functionality"""
    print("Testing login...")
    response = requests.post(f"{BASE_URL}/login", data={
        'email': 'razavcf@gmail.com',
        'password': 'admin123'
    }, allow_redirects=False)
    
    print(f"Login response: {response.status_code}")
    return response.cookies

def test_system_status(cookies):
    """Test system status API"""
    print("Testing system status...")
    response = requests.get(f"{BASE_URL}/api/system_status", cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print("System Status:")
        for key, value in data.items():
            print(f"  {key}: {value}")
    else:
        print(f"Failed to get system status: {response.status_code}")

def test_generate_key(cookies):
    """Test key generation"""
    print("Testing key generation...")
    response = requests.post(f"{BASE_URL}/api/generate_key", 
                           json={'user_email': 'razavcf@gmail.com'},
                           cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Key generation result: {data}")
        return data.get('key_id')
    else:
        print(f"Failed to generate key: {response.status_code}")
        return None

def test_send_email(cookies):
    """Test email sending"""
    print("Testing email sending...")
    email_data = {
        'sender': 'razavcf@gmail.com',
        'recipient': 'test@example.com',
        'subject': 'Test QuMail Email',
        'content': 'This is a test email from QuMail quantum secure email client.',
        'encryption_key': 'auto',
        'priority': 'normal'
    }
    
    response = requests.post(f"{BASE_URL}/api/send_email", 
                           json=email_data,
                           cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Email send result: {data}")
    else:
        print(f"Failed to send email: {response.status_code}")
        print(f"Response: {response.text}")

def main():
    """Run all tests"""
    print("QuMail Flask Application Test")
    print("=" * 40)
    
    try:
        # Test login
        cookies = test_login()
        
        # Test system status
        test_system_status(cookies)
        
        # Test key generation
        key_id = test_generate_key(cookies)
        
        # Test email sending
        test_send_email(cookies)
        
        print("\nAll tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask application.")
        print("Make sure the Flask app is running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()