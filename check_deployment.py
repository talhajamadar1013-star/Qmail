#!/usr/bin/env python3
"""
QuMail Pre-deployment Checker
Run this script to verify your application is ready for Render deployment
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Need Python 3.8+")
        return False

def check_requirements():
    """Check if all requirements can be installed"""
    print("\n📦 Checking requirements.txt...")
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        print(f"✅ Found {len(requirements)} requirements")
        
        # Try to check if key packages can be imported
        key_packages = ['flask', 'psycopg2', 'cryptography', 'web3']
        for package in key_packages:
            try:
                importlib.import_module(package.replace('-', '_'))
                print(f"✅ {package} is available")
            except ImportError:
                print(f"⚠️  {package} not installed (will be installed on Render)")
        
        return True
        
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def check_environment_files():
    """Check for necessary configuration files"""
    print("\n⚙️  Checking configuration files...")
    
    files_to_check = [
        ('render.yaml', 'Render configuration'),
        ('Procfile', 'Process configuration'),
        ('runtime.txt', 'Python runtime'),
        ('wsgi.py', 'WSGI entry point'),
        ('gunicorn.conf.py', 'Gunicorn configuration'),
        ('env.example', 'Environment variables template')
    ]
    
    all_good = True
    for filename, description in files_to_check:
        if os.path.exists(filename):
            print(f"✅ {filename} - {description}")
        else:
            print(f"❌ {filename} missing - {description}")
            all_good = False
    
    return all_good

def check_app_structure():
    """Check if the app structure is correct"""
    print("\n🏗️  Checking application structure...")
    
    required_paths = [
        'qumail_client/app.py',
        'qumail_client/templates/',
        'config/settings.py'
    ]
    
    all_good = True
    for path in required_paths:
        if os.path.exists(path):
            print(f"✅ {path}")
        else:
            print(f"❌ {path} missing")
            all_good = False
    
    return all_good

def check_environment_variables():
    """Check for required environment variables"""
    print("\n🔐 Checking environment variables...")
    
    # Load .env if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded")
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping .env file")
    
    required_vars = ['SECRET_KEY']
    optional_vars = ['DATABASE_URL', 'NEON_DB_HOST', 'PINATA_API_KEY']
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} not set (should be set in Render)")
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"ℹ️  {var} not set (optional)")
    
    return True

def test_local_startup():
    """Test if the app can start locally"""
    print("\n🚀 Testing local startup...")
    
    try:
        # Set test environment variables
        os.environ['FLASK_ENV'] = 'development'
        os.environ['PORT'] = '5000'
        
        # Try to import the app
        sys.path.insert(0, os.getcwd())
        from qumail_client.app import app
        
        print("✅ App can be imported successfully")
        
        # Test app context
        with app.app_context():
            print("✅ App context works")
        
        return True
        
    except Exception as e:
        print(f"❌ App startup failed: {e}")
        return False

def main():
    """Main check routine"""
    print("🔍 QuMail Pre-deployment Checker")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_requirements,
        check_environment_files,
        check_app_structure,
        check_environment_variables,
        test_local_startup
    ]
    
    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"✅ Passed: {sum(results)}/{len(results)} checks")
    
    if all(results):
        print("\n🎉 Your application is ready for Render deployment!")
        print("\nNext steps:")
        print("1. Push your code to GitHub")
        print("2. Connect to Render and deploy")
        print("3. Set environment variables in Render dashboard")
        print("4. Monitor deployment logs")
    else:
        print("\n⚠️  Please fix the issues above before deploying")
        print("\n📚 Check RENDER_DEPLOYMENT.md for detailed instructions")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)