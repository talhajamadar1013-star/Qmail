#!/usr/bin/env python3
"""
QuMail Key Manager Startup Script
Initializes database and starts the Flask API server
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask', 'sqlalchemy', 'psycopg2', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment():
    """Check if environment variables are configured"""
    from config.settings import load_config
    
    try:
        config = load_config()
        
        if not config.NEON_DB_HOST:
            print("❌ NEON_DB_HOST not configured")
            print("Please set up your .env file with database credentials")
            return False
        
        if not config.NEON_DB_USER:
            print("❌ NEON_DB_USER not configured")
            return False
        
        if not config.NEON_DB_PASSWORD:
            print("❌ NEON_DB_PASSWORD not configured")
            return False
        
        print("✅ Environment configuration looks good")
        print(f"   Database Host: {config.NEON_DB_HOST}")
        print(f"   Database Name: {config.NEON_DB_NAME}")
        print(f"   Database User: {config.NEON_DB_USER}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking environment: {e}")
        return False

def initialize_database():
    """Initialize database tables"""
    print("\n🗄️  Initializing database...")
    
    try:
        from key_manager.database.init_db import create_database_tables, verify_database_connection
        
        # Verify connection first
        if not verify_database_connection():
            return False
        
        # Create tables
        if not create_database_tables():
            return False
        
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_api_server():
    """Start the Flask API server"""
    print("\n🚀 Starting Key Manager API server...")
    
    try:
        from key_manager.app import app
        from config.settings import load_config
        
        config = load_config()
        port = int(os.environ.get('PORT', 5000))
        
        print(f"📡 Server will start at: http://localhost:{port}")
        print(f"🔧 Debug mode: {config.DEBUG}")
        print(f"🔑 Endpoints available:")
        print(f"   POST   /keys              - Generate new key")
        print(f"   GET    /keys/<key_id>     - Fetch key")
        print(f"   PATCH  /keys/<key_id>/use - Mark key as used")
        print(f"   GET    /keys/<key_id>/hash - Get key hash")
        print(f"   GET    /health            - Health check")
        print("\nPress Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=config.DEBUG
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

def show_usage():
    """Show usage instructions"""
    print("""
QuMail Key Manager - Usage Instructions

1. Environment Setup:
   Copy .env.example to .env and configure your settings:
   - NEON_DB_HOST: Your Neon database host
   - NEON_DB_USER: Database username  
   - NEON_DB_PASSWORD: Database password
   - NEON_DB_NAME: Database name

2. Install Dependencies:
   pip install -r requirements.txt

3. Start the Service:
   python key_manager/start.py

4. Test the API:
   python key_manager/test_api.py

API Endpoints:
- POST /keys                 - Generate new quantum key
- GET /keys/<key_id>         - Fetch key for encryption/decryption
- PATCH /keys/<key_id>/use   - Mark key as used (OTP requirement)
- GET /keys/<key_id>/hash    - Get key hash for verification
- GET /health                - Service health check

Authentication:
- Add 'Authorization: Bearer <token>' header
- Add 'X-User-ID: <user_email>' header
""")

def main():
    """Main startup function"""
    print("🌟 QuMail Key Manager Startup")
    print("=" * 50)
    
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
        return
    
    # Check if init-only flag is provided
    init_only = len(sys.argv) > 1 and sys.argv[1] in ['--init-only', 'init']
    
    # Step 1: Check dependencies
    print("1️⃣  Checking dependencies...")
    if not check_dependencies():
        return
    print("✅ All dependencies available")
    
    # Step 2: Check environment
    print("\n2️⃣  Checking environment configuration...")
    if not check_environment():
        print("\n💡 Setup Instructions:")
        print("1. Copy .env.example to .env")
        print("2. Configure your Neon database credentials")
        print("3. Run this script again")
        return
    
    # Step 3: Initialize database
    print("\n3️⃣  Initializing database...")
    if not initialize_database():
        print("❌ Database initialization failed")
        return
    
    if init_only:
        print("\n✅ Database initialization completed!")
        print("Run 'python key_manager/start.py' to start the API server")
        return
    
    # Step 4: Start API server
    print("\n4️⃣  Starting API server...")
    start_api_server()

if __name__ == "__main__":
    main()