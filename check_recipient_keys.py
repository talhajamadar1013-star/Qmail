#!/usr/bin/env python3
import os, sys
sys.path.insert(0, '.')
from qumail_client.embedded_km.neon_key_manager import NeonKeyManager
from config.settings import load_config

config = load_config()
km = NeonKeyManager(config)

# Check recipient keys
recipient = 'jauwwad.nallamandu123@gmail.com'
keys = km.get_user_keys(recipient, include_expired=True)

print(f'Keys for {recipient}:')
for key in keys:
    print(f'  Key ID: {key.get("key_id", "N/A")}')
    print(f'  Purpose: {key.get("purpose", "N/A")}')
    print(f'  Active: {key.get("is_active", False)}')
    print(f'  Expired: {key.get("expired", True)}')
    print()

print(f'Total keys found: {len(keys)}')