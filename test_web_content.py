#!/usr/bin/env python3
"""
Test what encrypted content the web interface is getting for email
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'qumail_client'))

from embedded_km.neon_key_manager import NeonKeyManager
from crypto.quantum_encryption import QuantumEncryption
from config.settings import load_config

# Initialize
config = load_config()
key_manager = NeonKeyManager(config)
crypto = QuantumEncryption(config)

# Get email content like the web interface does  
user_id = 'jauwwad.nallamandu123@gmail.com'  # orchid receiver (user_id is email)
email_id = 41  # From diagnose output (as integer)

print(f"Testing email content retrieval for email {email_id}")
print(f"User: {user_id}")
print("="*60)

# Get email like inbox route does
inbox_emails = key_manager.get_user_inbox(user_id)
inbox_email = None
for email in inbox_emails:
    if email['id'] == email_id:
        inbox_email = email
        break

if inbox_email:
    print("INBOX ROUTE - Email content:")
    print(f"  Email ID: {inbox_email['id']}")
    print(f"  Type: {inbox_email['type']}")
    print(f"  Subject: {inbox_email['subject']}")
    print(f"  Key ID: {inbox_email['encryption_key_id']}")
    print(f"  Encrypted content: {inbox_email['encrypted_content']}")
    print(f"  Content length: {len(inbox_email['encrypted_content']) if inbox_email['encrypted_content'] else 0}")
    print()

# Get email like view_email route does - check both sent and received
print("VIEW_EMAIL ROUTE - Looking for email...")

# Check sent emails
sent_emails = key_manager.get_sent_emails(user_id)
sent_email = None
for email in sent_emails:
    if email['id'] == email_id:
        sent_email = email
        print("Found in SENT emails:")
        print(f"  Email ID: {email['id']}")
        print(f"  Subject: {email['subject']}")
        print(f"  Key ID: {email.get('key_id')}")
        print(f"  Encrypted content: {email.get('content')}")
        print(f"  Content length: {len(email.get('content', ''))}")
        break

# Check received emails
received_emails = key_manager.get_received_emails(user_id)
received_email = None
for email in received_emails:
    if email['id'] == email_id:
        received_email = email
        print("Found in RECEIVED emails:")
        print(f"  Email ID: {email['id']}")
        print(f"  Subject: {email['subject']}")
        print(f"  Key ID: {email.get('encryption_key_id')}")
        print(f"  Encrypted content: {email.get('encrypted_content')}")
        print(f"  Content length: {len(email.get('encrypted_content', ''))}")
        break

print()
print("COMPARISON:")
if inbox_email and received_email:
    inbox_content = inbox_email['encrypted_content']
    received_content = received_email['encrypted_content']
    print(f"Inbox content:    '{inbox_content}'")
    print(f"Received content: '{received_content}'")
    print(f"Contents match: {inbox_content == received_content}")
else:
    print("Could not find email in both sources for comparison")

# Test decryption with the content from inbox
if inbox_email:
    key_id = inbox_email['encryption_key_id']
    encrypted_content = inbox_email['encrypted_content']
    
    # Get the key
    user_keys = key_manager.get_user_keys(user_id, include_expired=True)
    decryption_key = None
    for key in user_keys:
        if key['key_id'] == key_id:
            decryption_key = key['key_data']
            break
    
    if decryption_key and encrypted_content:
        print(f"\nTesting decryption with inbox content:")
        print(f"Key found: {bool(decryption_key)}")
        try:
            decrypted = crypto.decrypt_message(encrypted_content, decryption_key)
            print(f"✅ DECRYPTED MESSAGE: '{decrypted}'")
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
    else:
        print(f"❌ Missing key or content for decryption")