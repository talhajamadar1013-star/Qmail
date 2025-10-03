#!/usr/bin/env python3
"""
QuMail Application Entry Point for Production Deployment
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

logger.info(f"Project root: {project_root}")
logger.info(f"Python path: {sys.path[:3]}")

try:
    # Import the Flask app
    from qumail_client.app import app
    logger.info("Successfully imported Flask app")
    
    # Test app creation
    with app.app_context():
        logger.info("Flask app context works")
        
except Exception as e:
    logger.error(f"Failed to import Flask app: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Files in current directory: {os.listdir('.')}")
    raise

if __name__ == "__main__":
    try:
        # Get port from environment variable (Render sets this)
        port = int(os.getenv('PORT', 10000))
        host = os.getenv('HOST', '0.0.0.0')
        
        logger.info(f"Starting QuMail on {host}:{port}")
        logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)