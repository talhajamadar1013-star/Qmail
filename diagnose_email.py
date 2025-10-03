"""
Diagnostic script to check email and key status
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def diagnose_email_issue():
    """Diagnose why emails can't be decrypted"""
    
    print("=" * 70)
    print("QuMail Decryption Diagnostic Tool")
    print("=" * 70)
    print()
    
    user_email = input("Enter your email address: ").strip()
    
    if not user_email:
        print("Error: Email address required")
        return
    
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check sent emails
                print(f"\n📤 SENT EMAILS for {user_email}")
                print("-" * 70)
                cur.execute("""
                    SELECT id, recipient, subject, encryption_key_id, sent_at
                    FROM email_statistics
                    WHERE user_id = %s AND email_type = 'sent'
                    ORDER BY sent_at DESC
                    LIMIT 10
                """, (user_email,))
                
                sent_emails = cur.fetchall()
                
                if not sent_emails:
                    print("  No sent emails found")
                else:
                    for email in sent_emails:
                        print(f"\n  Email ID: {email['id']}")
                        print(f"  To: {email['recipient']}")
                        print(f"  Subject: {email['subject']}")
                        print(f"  Key ID: {email['encryption_key_id']}")
                        print(f"  Sent: {email['sent_at']}")
                        
                        # Check if key exists for sender
                        cur.execute("""
                            SELECT key_id, user_id, is_active, expires_at
                            FROM quantum_keys
                            WHERE key_id = %s
                        """, (email['encryption_key_id'],))
                        
                        keys = cur.fetchall()
                        
                        if not keys:
                            print(f"  ❌ KEY NOT FOUND - This is the problem!")
                        else:
                            print(f"  Keys found: {len(keys)}")
                            for key in keys:
                                status = "✅ Active" if key['is_active'] else "❌ Inactive"
                                owner_status = "✅ You have it" if key['user_id'] == user_email else f"👤 Owned by {key['user_id']}"
                                print(f"    - {status}, {owner_status}, Expires: {key['expires_at']}")
                
                # Check received emails
                print(f"\n📥 RECEIVED EMAILS for {user_email}")
                print("-" * 70)
                cur.execute("""
                    SELECT id, sender, subject, encryption_key_id, sent_at
                    FROM email_statistics
                    WHERE user_id = %s AND email_type = 'received'
                    ORDER BY sent_at DESC
                    LIMIT 10
                """, (user_email,))
                
                received_emails = cur.fetchall()
                
                if not received_emails:
                    print("  No received emails found")
                else:
                    for email in received_emails:
                        print(f"\n  Email ID: {email['id']}")
                        print(f"  From: {email['sender']}")
                        print(f"  Subject: {email['subject']}")
                        print(f"  Key ID: {email['encryption_key_id']}")
                        print(f"  Received: {email['sent_at']}")
                        
                        # Check if key exists for recipient
                        cur.execute("""
                            SELECT key_id, user_id, is_active, expires_at
                            FROM quantum_keys
                            WHERE key_id = %s
                        """, (email['encryption_key_id'],))
                        
                        keys = cur.fetchall()
                        
                        if not keys:
                            print(f"  ❌ KEY NOT FOUND - Key was never shared with you!")
                        else:
                            has_access = any(k['user_id'] == user_email for k in keys)
                            if not has_access:
                                print(f"  ❌ KEY NOT SHARED - You don't have access to this key!")
                                print(f"     Key belongs to: {', '.join(set(k['user_id'] for k in keys))}")
                            else:
                                print(f"  ✅ You have access to this key")
                                for key in keys:
                                    if key['user_id'] == user_email:
                                        status = "✅ Active" if key['is_active'] else "❌ Inactive"
                                        print(f"     Status: {status}, Expires: {key['expires_at']}")
                
                # Check all user keys
                print(f"\n🔑 ALL KEYS for {user_email}")
                print("-" * 70)
                cur.execute("""
                    SELECT key_id, purpose, recipient, is_active, expires_at, created_at
                    FROM quantum_keys
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_email,))
                
                all_keys = cur.fetchall()
                
                if not all_keys:
                    print("  No keys found")
                else:
                    print(f"  Total keys: {len(all_keys)}")
                    for key in all_keys[:10]:  # Show first 10
                        status = "✅ Active" if key['is_active'] else "❌ Inactive"
                        print(f"\n  Key ID: {key['key_id'][:36]}")
                        print(f"  Purpose: {key['purpose']}")
                        print(f"  Recipient: {key['recipient']}")
                        print(f"  Status: {status}")
                        print(f"  Expires: {key['expires_at']}")
                
                # Check database schema
                print(f"\n🗄️  DATABASE SCHEMA CHECK")
                print("-" * 70)
                cur.execute("""
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_name = 'quantum_keys'
                    AND constraint_type = 'PRIMARY KEY'
                """)
                
                pk = cur.fetchone()
                if pk:
                    print(f"  Primary Key: {pk['constraint_name']}")
                    
                    # Check if it's composite
                    cur.execute("""
                        SELECT column_name
                        FROM information_schema.key_column_usage
                        WHERE constraint_name = %s
                        ORDER BY ordinal_position
                    """, (pk['constraint_name'],))
                    
                    columns = [row['column_name'] for row in cur.fetchall()]
                    print(f"  Columns: {', '.join(columns)}")
                    
                    if len(columns) == 2 and 'key_id' in columns and 'user_id' in columns:
                        print(f"  ✅ Schema is correct for key sharing!")
                    elif len(columns) == 1 and columns[0] == 'key_id':
                        print(f"  ⚠️  Schema NOT migrated - run migrate_keys_table.py!")
                    else:
                        print(f"  ❓ Unexpected schema configuration")
                
                print("\n" + "=" * 70)
                print("RECOMMENDATIONS:")
                print("=" * 70)
                
                # Provide recommendations
                if len(columns) == 1:
                    print("1. ⚠️  RUN MIGRATION: python migrate_keys_table.py")
                    print("   This is REQUIRED for key sharing to work!")
                
                print("2. 📧 TEST WITH NEW EMAIL: Send a new email after migration")
                print("3. 🔑 OLD EMAILS: May need keys shared retroactively")
                print("4. 🐛 DEBUG PAGE: Visit /debug/keys to test encryption")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    diagnose_email_issue()
