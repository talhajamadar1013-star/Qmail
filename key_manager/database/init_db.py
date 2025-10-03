"""
Database initialization and migration scripts for Neon Database
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import load_config
from key_manager.database.models import Base, DatabaseManager

def create_database_tables():
    """Create all database tables if they don't exist"""
    try:
        config = load_config()
        db_url = config.get_database_url()
        
        print(f"Connecting to Neon Database...")
        print(f"Host: {config.NEON_DB_HOST}")
        print(f"Database: {config.NEON_DB_NAME}")
        
        # Create database manager
        db_manager = DatabaseManager(db_url)
        
        print("✅ Database tables created successfully!")
        print("\nCreated tables:")
        print("- quantum_keys: Stores OTP quantum keys")
        print("- email_metadata: Stores email metadata and IPFS hashes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

def verify_database_connection():
    """Verify database connection and show table info"""
    try:
        config = load_config()
        db_url = config.get_database_url()
        
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            # Test connection
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
            
            # Check tables
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            if tables:
                print(f"\n📊 Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠️  No tables found. Run create_database_tables() first.")
            
            # Check quantum_keys table structure
            if any('quantum_keys' in str(table) for table in tables):
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'quantum_keys'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                print(f"\n🔑 quantum_keys table structure:")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    print(f"  - {col[0]}: {col[1]} ({nullable})")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def seed_test_data():
    """Insert test data for development"""
    try:
        from key_manager.database.operations import QuantumKeyService, EmailMetadataService
        
        print("🌱 Seeding test data...")
        
        # Create services
        key_service = QuantumKeyService()
        email_service = EmailMetadataService()
        
        # Generate test quantum keys
        test_users = ['alice@example.com', 'bob@example.com', 'charlie@example.com']
        
        for user in test_users:
            key_data = key_service.generate_quantum_key(user, key_length=256)
            print(f"  ✅ Generated key for {user}: {key_data['key_id']}")
        
        # Create test email metadata
        test_email = {
            'sender_email': 'alice@example.com',
            'recipient_email': 'bob@example.com',
            'key_id': 'test_key_123',
            'ipfs_hash': 'QmTestHash123456789',
            'subject_hash': 'abc123def456'
        }
        
        email_id = email_service.store_email_metadata(test_email)
        print(f"  ✅ Created test email metadata: {email_id}")
        
        print("🎉 Test data seeded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding test data: {e}")
        return False

def main():
    """Main database setup function"""
    print("🚀 QuMail Database Setup for Neon")
    print("=" * 50)
    
    # Check environment variables
    config = load_config()
    if not config.NEON_DB_HOST:
        print("❌ NEON_DB_HOST not configured. Please set up your .env file.")
        return
    
    print(f"Database Host: {config.NEON_DB_HOST}")
    print(f"Database Name: {config.NEON_DB_NAME}")
    print(f"Database User: {config.NEON_DB_USER}")
    print("-" * 50)
    
    # Step 1: Verify connection
    print("\n1️⃣  Verifying database connection...")
    if not verify_database_connection():
        return
    
    # Step 2: Create tables
    print("\n2️⃣  Creating database tables...")
    if not create_database_tables():
        return
    
    # Step 3: Verify tables were created
    print("\n3️⃣  Verifying table creation...")
    verify_database_connection()
    
    # Step 4: Seed test data (optional)
    print("\n4️⃣  Would you like to seed test data? (y/n): ", end="")
    choice = input().lower().strip()
    
    if choice in ['y', 'yes']:
        seed_test_data()
    
    print(f"\n🎉 Database setup complete!")
    print(f"\nNext steps:")
    print(f"1. Start the Key Manager API: python key_manager/app.py")
    print(f"2. Launch QuMail Client: python qumail_client/main.py")

if __name__ == "__main__":
    main()