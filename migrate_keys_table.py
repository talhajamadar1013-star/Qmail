"""
Migration script to allow key sharing between users
This updates the quantum_keys table to allow the same key_id for multiple users
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def migrate_database():
    """Migrate quantum_keys table to support key sharing"""
    try:
        print("Connecting to database...")
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                print("Starting migration...")
                
                # Step 1: Check if we need to migrate
                cur.execute("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'quantum_keys' 
                    AND constraint_type = 'PRIMARY KEY'
                """)
                
                pk_exists = cur.fetchone()
                
                if pk_exists:
                    print("Found existing PRIMARY KEY constraint, migrating...")
                    
                    # Step 2: Drop the old primary key
                    cur.execute("""
                        ALTER TABLE quantum_keys 
                        DROP CONSTRAINT IF EXISTS quantum_keys_pkey CASCADE
                    """)
                    print("✓ Dropped old PRIMARY KEY constraint")
                    
                    # Step 3: Add composite primary key (key_id + user_id)
                    cur.execute("""
                        ALTER TABLE quantum_keys 
                        ADD PRIMARY KEY (key_id, user_id)
                    """)
                    print("✓ Added composite PRIMARY KEY (key_id, user_id)")
                    
                    # Step 4: Recreate index
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_quantum_keys_user_id 
                        ON quantum_keys(user_id)
                    """)
                    print("✓ Recreated user_id index")
                    
                    conn.commit()
                    print("\n✅ Migration completed successfully!")
                    print("   Keys can now be shared between users")
                    
                else:
                    # Check if composite key already exists
                    cur.execute("""
                        SELECT constraint_name 
                        FROM information_schema.table_constraints 
                        WHERE table_name = 'quantum_keys' 
                        AND constraint_type = 'PRIMARY KEY'
                        AND constraint_name LIKE '%key_id%user_id%'
                    """)
                    
                    if cur.fetchone():
                        print("✅ Database already migrated - composite PRIMARY KEY exists")
                    else:
                        print("⚠️  No PRIMARY KEY found, creating composite key...")
                        cur.execute("""
                            ALTER TABLE quantum_keys 
                            ADD PRIMARY KEY (key_id, user_id)
                        """)
                        conn.commit()
                        print("✅ Composite PRIMARY KEY added")
                
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nIf you see a 'duplicate key value' error, it means you have")
        print("duplicate key_ids in your database. You may need to manually clean them up.")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("QuMail Database Migration: Enable Key Sharing")
    print("=" * 60)
    print()
    
    response = input("This will modify your database structure. Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_database()
    else:
        print("Migration cancelled")
