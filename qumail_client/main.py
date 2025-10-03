#!/usr/bin/env python3
"""
QuMail - Quantum Secure Email Client
Main application entry point
"""

import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import load_config

def main():
    """Main application entry point"""
    print("QuMail - Quantum Secure Email Client")
    print("=====================================\n")
    print("QuMail is now running as a Flask web application.")
    print("Please use the following command to start the web interface:")
    print("\n  python qumail_client/app.py\n")
    print("Then open your browser and go to: http://127.0.0.1:5000")
    print("\nNote: The PyQt5 desktop interface has been replaced with a web interface.")

if __name__ == "__main__":
    main()