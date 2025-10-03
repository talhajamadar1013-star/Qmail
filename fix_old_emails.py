"""
Script to retroactively share keys for old emails
Run this AFTER database migration to fix old emails that can't be decrypted
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qumail_client.embedded_km.neon_key_manager import NeonKeyManager
from config.settings import load_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def fix_old_emails():
    """Share keys for old emails retroactively"""
    
    print("=" * 70)
    print("QuMail: Retroactive Key Sharing for Old Emails")
    print("=" * 70)
    print()
    print("⚠️  This script will share encryption keys for your old emails")
    print("   so recipients can decrypt them.")
    print()
    
    your_email = input("Enter your email address: ").strip()
    
    if not your_email:
        print("Error: Email required")
        return
    
    print(f"\n🔄 Processing emails for {your_email}...")
    print()
    
    try:
        # Initialize key manager
        config = load_config()
        km = NeonKeyManager(config)
        
        # Get all sent emails
        sent_emails = km.get_sent_emails(your_email, limit=100)
        
        print(f"📧 Found {len(sent_emails)} sent emails")
        print()
        
        if not sent_emails:
            print("No emails to process")
            return
        
        success_count = 0
        fail_count = 0
        already_shared_count = 0
        
        for i, email in enumerate(sent_emails, 1):
            key_id = email.get('encryption_key_id') or email.get('key_id')
            recipient = email.get('recipient')
            subject = email.get('subject', 'No subject')
            
            print(f"[{i}/{len(sent_emails)}] {subject[:50]}")
            print(f"  To: {recipient}")
            print(f"  Key: {key_id[:36] if key_id else 'None'}...")
            
            if not key_id:
                print(f"  ⚠️  No key ID found, skipping")
                fail_count += 1
                continue
            
            if not recipient:
                print(f"  ⚠️  No recipient found, skipping")
                fail_count += 1
                continue
            
            try:
                # Try to share key
                result = km.share_key_with_recipient(key_id, your_email, recipient)
                
                if result:
                    print(f"  ✅ Key shared successfully")
                    success_count += 1
                else:
                    print(f"  ⚠️  Key might already be shared or sender doesn't have it")
                    already_shared_count += 1
                    
            except Exception as e:
                error_msg = str(e)
                if "duplicate key value" in error_msg.lower():
                    print(f"  ℹ️  Key already shared")
                    already_shared_count += 1
                elif "not found" in error_msg.lower():
                    print(f"  ❌ Key not found in database")
                    fail_count += 1
                else:
                    print(f"  ❌ Error: {error_msg}")
                    fail_count += 1
            
            print()
        
        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✅ Successfully shared: {success_count}")
        print(f"ℹ️  Already shared: {already_shared_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"📧 Total processed: {len(sent_emails)}")
        print()
        
        if success_count > 0:
            print("🎉 Keys have been shared! Recipients should now be able to decrypt.")
        
        if fail_count > 0:
            print("⚠️  Some keys couldn't be shared. Possible reasons:")
            print("   - Key was deleted or expired")
            print("   - Database migration not completed")
            print("   - Key never existed (shouldn't happen)")
        
        print()
        print("💡 TIP: Send a test email to verify everything works!")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.exception("Failed to process emails")

if __name__ == "__main__":
    fix_old_emails()
