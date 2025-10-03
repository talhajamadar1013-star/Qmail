#!/usr/bin/env python3
"""
QuMail Setup and Initialization Script
Sets up embedded Key Manager, local storage, and validates configuration
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    env_path = project_root / '.env'
    env_example_path = project_root / '.env.example'
    
    if not env_path.exists() and env_example_path.exists():
        print("📝 Creating .env file from .env.example...")
        
        with open(env_example_path, 'r') as src:
            content = src.read()
        
        with open(env_path, 'w') as dst:
            dst.write(content)
        
        print("✅ .env file created!")
        print("⚠️  Please edit .env with your actual credentials")
        return False
    
    return env_path.exists()

def check_dependencies():
    """Check if required dependencies are available"""
    required_packages = {
        'cryptography': 'cryptography',
        'web3': 'web3',
        'requests': 'requests',
        'dotenv': 'python-dotenv'
    }
    
    optional_packages = {
        'PyQt5': 'PyQt5',
        'PySide6': 'PySide6'
    }
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    for package, pip_name in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_required.append(pip_name)
            print(f"❌ {package}")
    
    # Check optional GUI packages
    gui_available = False
    for package, pip_name in optional_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} (GUI)")
            gui_available = True
            break
        except ImportError:
            missing_optional.append(pip_name)
            print(f"⚠️  {package} (optional GUI)")
    
    # Check tkinter (built into Python)
    try:
        import tkinter
        print(f"✅ tkinter (built-in GUI)")
        gui_available = True
    except ImportError:
        print(f"❌ tkinter (no GUI available)")
    
    if missing_required:
        print(f"\n📦 Install missing required packages:")
        print(f"pip install {' '.join(missing_required)}")
        return False
    
    if not gui_available:
        print(f"\n⚠️  No GUI framework available!")
        print(f"Install one of: {' '.join(missing_optional)}")
        print(f"Or use: brew install pyqt@5  # on macOS")
        return False
    
    if missing_optional:
        print(f"\n💡 Optional GUI packages available for install:")
        print(f"pip install {' '.join(missing_optional)}")
    
    return True

def validate_configuration():
    """Validate configuration settings"""
    try:
        from config.settings import load_config
        config = load_config()
        
        print(f"🔧 Configuration validation:")
        print(f"   Environment: {config.ENVIRONMENT}")
        print(f"   Debug mode: {config.DEBUG}")
        print(f"   Embedded KM: {config.ENABLE_EMBEDDED_KM}")
        print(f"   Blockchain: {config.POLYGON_NETWORK_NAME}")
        print(f"   Local storage: {config.LOCAL_DATA_PATH}")
        
        # Check critical settings
        issues = []
        
        if config.ENABLE_BLOCKCHAIN_VERIFICATION and not config.POLYGON_RPC_URL:
            issues.append("POLYGON_RPC_URL not configured for blockchain verification")
        
        if config.ENABLE_IPFS_STORAGE and not config.PINATA_API_KEY:
            issues.append("PINATA_API_KEY not configured for IPFS storage")
        
        if not config.KEY_ENCRYPTION_PASSWORD:
            issues.append("KEY_ENCRYPTION_PASSWORD not set (using default - not secure)")
        
        if config.NEON_DB_HOST and not config.NEON_DB_PASSWORD:
            issues.append("NEON_DB_PASSWORD not configured")
        
        if issues:
            print(f"\n⚠️  Configuration issues:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Configuration looks good!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def initialize_embedded_km():
    """Initialize embedded Key Manager"""
    try:
        print(f"🔑 Initializing Embedded Key Manager...")
        
        from config.settings import load_config
        from qumail_client.embedded_km.local_key_manager import get_embedded_key_manager
        
        config = load_config()
        km = get_embedded_key_manager(config)
        
        # Test key generation
        test_key = km.generate_quantum_key("setup_test@qumail.local", 64)
        print(f"   ✅ Generated test key: {test_key['key_id']}")
        
        # Cleanup test key
        km.mark_key_used(test_key['key_id'], "setup_test")
        
        # Get statistics
        stats = km.get_statistics()
        print(f"   📊 Database: {stats.get('total_keys', 0)} keys total")
        print(f"   💾 Storage: {config.LOCAL_DATA_PATH}")
        
        print("✅ Embedded Key Manager initialized!")
        return True
        
    except Exception as e:
        print(f"❌ Key Manager initialization failed: {e}")
        return False

def test_blockchain_connection():
    """Test blockchain connection (optional)"""
    try:
        from config.settings import load_config
        config = load_config()
        
        if not config.ENABLE_BLOCKCHAIN_VERIFICATION:
            print("⏭️  Blockchain verification disabled")
            return True
        
        if not config.POLYGON_RPC_URL:
            print("⚠️  No blockchain RPC URL configured")
            return True
        
        print(f"🔗 Testing blockchain connection...")
        
        from web3 import Web3
        
        # Try primary RPC
        web3 = Web3(Web3.HTTPProvider(config.get_polygon_rpc_url()))
        
        if web3.is_connected():
            latest_block = web3.eth.block_number
            print(f"   ✅ Connected to {config.POLYGON_NETWORK_NAME}")
            print(f"   📦 Latest block: {latest_block}")
            print(f"   🔗 Chain ID: {config.POLYGON_CHAIN_ID}")
            return True
        else:
            print(f"   ❌ Failed to connect to blockchain")
            return False
            
    except Exception as e:
        print(f"❌ Blockchain connection error: {e}")
        return False

def test_ipfs_connection():
    """Test IPFS (Pinata) connection (optional)"""
    try:
        from config.settings import load_config
        config = load_config()
        
        if not config.ENABLE_IPFS_STORAGE:
            print("⏭️  IPFS storage disabled")
            return True
        
        if not config.PINATA_API_KEY:
            print("⚠️  No Pinata API key configured")
            return True
        
        print(f"📁 Testing IPFS (Pinata) connection...")
        
        import requests
        
        headers = {
            'pinata_api_key': config.PINATA_API_KEY,
            'pinata_secret_api_key': config.PINATA_SECRET_KEY
        }
        
        response = requests.get(
            f"{config.PINATA_BASE_URL}/data/testAuthentication",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Connected to Pinata IPFS")
            print(f"   📊 Status: {result.get('message', 'OK')}")
            return True
        else:
            print(f"   ❌ Pinata authentication failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ IPFS connection error: {e}")
        return False

def create_desktop_shortcut():
    """Create desktop shortcut for QuMail (optional)"""
    try:
        if sys.platform == "darwin":  # macOS
            print("🖥️  macOS desktop shortcut creation not implemented")
        elif sys.platform == "win32":  # Windows
            print("🖥️  Windows desktop shortcut creation not implemented")
        elif sys.platform.startswith("linux"):  # Linux
            print("🖥️  Linux desktop shortcut creation not implemented")
        
        return True
        
    except Exception as e:
        print(f"❌ Desktop shortcut creation error: {e}")
        return False

def display_summary(config):
    """Display setup summary"""
    print(f"\n🎉 QuMail Setup Complete!")
    print(f"=" * 60)
    print(f"📧 QuMail - Quantum Secure Email Client")
    print(f"🔐 Encryption: {config.ENCRYPTION_ALGORITHM} ({config.QUANTUM_PROTOCOL})")
    print(f"🔑 Key Manager: {'Embedded (Local)' if config.ENABLE_EMBEDDED_KM else 'External API'}")
    print(f"🌐 Blockchain: {config.POLYGON_NETWORK_NAME}")
    print(f"📁 IPFS: {'Enabled (Pinata)' if config.ENABLE_IPFS_STORAGE else 'Disabled'}")
    print(f"💾 Local storage: {config.LOCAL_DATA_PATH}")
    print(f"")
    print(f"🚀 Ready to launch QuMail!")
    print(f"")
    print(f"Next steps:")
    print(f"1. Start QuMail: python qumail_client/main.py")
    print(f"2. Configure your email account")
    print(f"3. Start sending quantum-secure emails!")
    print(f"")
    print(f"🔧 Configuration file: .env")
    print(f"📖 Documentation: docs/")

def main():
    """Main setup function"""
    print(f"🌟 QuMail - Quantum Secure Email Setup")
    print(f"=" * 50)
    
    # Step 1: Create .env file
    print(f"\n1️⃣  Environment Configuration")
    print(f"-" * 30)
    if not create_env_file():
        print(f"Please configure .env file and run setup again")
        return False
    
    # Step 2: Check dependencies
    print(f"\n2️⃣  Dependency Check")
    print(f"-" * 30)
    if not check_dependencies():
        return False
    
    # Step 3: Validate configuration
    print(f"\n3️⃣  Configuration Validation")
    print(f"-" * 30)
    if not validate_configuration():
        print(f"Please fix configuration issues in .env file")
        return False
    
    # Step 4: Initialize embedded Key Manager
    print(f"\n4️⃣  Key Manager Setup")
    print(f"-" * 30)
    if not initialize_embedded_km():
        return False
    
    # Step 5: Test blockchain (optional)
    print(f"\n5️⃣  Blockchain Test")
    print(f"-" * 30)
    test_blockchain_connection()
    
    # Step 6: Test IPFS (optional)
    print(f"\n6️⃣  IPFS Test")
    print(f"-" * 30)
    test_ipfs_connection()
    
    # Step 7: Create shortcuts (optional)
    print(f"\n7️⃣  Desktop Integration")
    print(f"-" * 30)
    create_desktop_shortcut()
    
    # Step 8: Display summary
    from config.settings import load_config
    config = load_config()
    display_summary(config)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n👋 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)