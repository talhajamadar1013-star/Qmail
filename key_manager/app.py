"""
QuMail Key Manager API
Flask application for managing quantum keys and providing secure key distribution
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import hashlib
import secrets
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import load_config
from key_manager.database.operations import QuantumKeyService, EmailMetadataService
from key_manager.quantum.key_generator import QuantumKeyGenerator

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for client connections

# Load configuration
config = load_config()

# Initialize services
key_service = QuantumKeyService()
email_service = EmailMetadataService()
quantum_generator = QuantumKeyGenerator()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'QuMail Key Manager',
        'version': '1.0.0'
    })

@app.route('/keys', methods=['POST'])
def generate_key():
    """
    Generate new quantum key
    
    Request body (optional):
    {
        "key_length": 256,
        "user_id": "user@example.com"
    }
    
    Response:
    {
        "key_id": "K123",
        "status": "unused"
    }
    """
    try:
        data = request.get_json() or {}
        
        user_id = data.get('user_id', 'anonymous')
        key_length = data.get('key_length', 256)
        
        # Validate key length
        if key_length < 64 or key_length > 4096:
            return jsonify({
                'error': 'key_length must be between 64 and 4096 bytes'
            }), 400
        
        # Generate quantum key
        key_data = key_service.generate_quantum_key(user_id, key_length)
        
        # Return simplified response as per API spec
        response = {
            'key_id': key_data['key_id'],
            'status': key_data['status']
        }
        
        app.logger.info(f"Generated quantum key {key_data['key_id']} for user {user_id}")
        
        return jsonify(response), 201
        
    except Exception as e:
        app.logger.error(f"Error generating quantum key: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/keys/<key_id>', methods=['GET'])
def fetch_key(key_id):
    """
    Fetch key for client
    
    Headers:
    - Authorization: Bearer <api_token>
    - X-User-ID: <user_id>
    
    Response:
    {
        "key_id": "K123",
        "key_bytes": "<encrypted key in hex>"
    }
    """
    try:
        # Get user ID from header
        user_id = request.headers.get('X-User-ID')
        api_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not user_id:
            return jsonify({
                'error': 'X-User-ID header is required'
            }), 400
        
        if not api_token:
            return jsonify({
                'error': 'Authorization header is required'
            }), 401
        
        # TODO: Validate API token (implement token validation logic)
        # For now, we'll accept any non-empty token
        
        # Retrieve key from database
        key_data = key_service.get_quantum_key(key_id, user_id)
        
        if not key_data:
            return jsonify({
                'error': 'Key not found or access denied'
            }), 404
        
        # Check if key is already used
        if key_data['status'] == 'used':
            return jsonify({
                'error': 'Key has already been used'
            }), 410  # Gone
        
        # Return key data as per API spec
        response = {
            'key_id': key_data['key_id'],
            'key_bytes': key_data['key_bytes'].hex()  # Convert to hex for JSON
        }
        
        app.logger.info(f"Fetched quantum key {key_id} for user {user_id}")
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error fetching quantum key {key_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/keys/<key_id>/use', methods=['PATCH'])
def mark_key_as_used(key_id):
    """
    Mark key as used
    
    Headers:
    - X-User-ID: <user_id>
    
    Response:
    {
        "key_id": "K123",
        "status": "used"
    }
    """
    try:
        user_id = request.headers.get('X-User-ID')
        
        if not user_id:
            return jsonify({
                'error': 'X-User-ID header is required'
            }), 400
        
        # Mark key as used
        success = key_service.mark_key_used(key_id, user_id)
        
        if not success:
            return jsonify({
                'error': 'Key not found'
            }), 404
        
        # Return response as per API spec
        response = {
            'key_id': key_id,
            'status': 'used'
        }
        
        app.logger.info(f"Marked key {key_id} as used by {user_id}")
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error marking key {key_id} as used: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/keys/<key_id>/hash', methods=['GET'])
def fetch_key_hash(key_id):
    """
    Fetch key hash for verification
    
    Response:
    {
        "key_id": "K123",
        "hash": "sha256hash"
    }
    """
    try:
        # Retrieve key from database
        with key_service.db_manager.get_session() as session:
            from key_manager.database.models import QuantumKey
            quantum_key = session.query(QuantumKey).filter(
                QuantumKey.key_id == key_id
            ).first()
            
            if not quantum_key:
                return jsonify({
                    'error': 'Key not found'
                }), 404
            
            # Generate SHA256 hash of the key
            key_hash = hashlib.sha256(quantum_key.key_bytes).hexdigest()
            
            # Return hash as per API spec
            response = {
                'key_id': key_id,
                'hash': key_hash
            }
            
            app.logger.info(f"Fetched hash for key {key_id}")
            
            return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error fetching hash for key {key_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/keys/<key_id>/blockchain', methods=['POST'])
def store_blockchain_hash(key_id):
    """
    Store blockchain transaction hash for key verification
    
    Request body:
    {
        "tx_hash": "0x1234567890abcdef...",
        "blockchain": "polygon_mumbai"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'tx_hash' not in data:
            return jsonify({
                'error': 'tx_hash is required'
            }), 400
        
        tx_hash = data['tx_hash']
        blockchain = data.get('blockchain', 'polygon_mumbai')
        
        # Store blockchain hash
        success = key_service.store_blockchain_hash(key_id, tx_hash)
        
        if not success:
            return jsonify({
                'error': 'Key not found'
            }), 404
        
        app.logger.info(f"Stored blockchain hash for key {key_id}: {tx_hash}")
        
        return jsonify({
            'message': 'Blockchain hash stored',
            'key_id': key_id,
            'tx_hash': tx_hash,
            'blockchain': blockchain,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error storing blockchain hash for key {key_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/v1/user/<user_id>/keys', methods=['GET'])
def get_user_keys(user_id):
    """
    Get all keys for a user
    
    Query parameters:
    - status: Filter by status (unused/used/expired)
    - limit: Maximum number of keys to return
    """
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', type=int, default=50)
        
        # Get user keys
        keys = key_service.get_user_keys(user_id, status)
        
        # Limit results
        if limit > 0:
            keys = keys[:limit]
        
        # Remove sensitive data from response
        safe_keys = []
        for key in keys:
            safe_key = {k: v for k, v in key.items() if k != 'key_bytes'}
            safe_keys.append(safe_key)
        
        return jsonify({
            'user_id': user_id,
            'total_keys': len(safe_keys),
            'keys': safe_keys
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error retrieving keys for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/v1/email/metadata', methods=['POST'])
def store_email_metadata():
    """
    Store email metadata
    
    Request body:
    {
        "sender_email": "sender@example.com",
        "recipient_email": "recipient@example.com",
        "key_id": "key123",
        "ipfs_hash": "QmHash123",
        "subject_hash": "subjectHash123"
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['sender_email', 'recipient_email', 'key_id']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({
                    'error': f'{field} is required'
                }), 400
        
        # Store email metadata
        email_id = email_service.store_email_metadata(data)
        
        app.logger.info(f"Stored email metadata {email_id}")
        
        return jsonify({
            'email_id': email_id,
            'message': 'Email metadata stored',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error storing email metadata: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    # Setup logging
    import logging
    if config.DEBUG:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
    
    # Initialize database
    try:
        from key_manager.database.models import get_database_manager
        db_manager = get_database_manager()
        app.logger.info("Database connection established")
    except Exception as e:
        app.logger.error(f"Database connection failed: {e}")
        sys.exit(1)
    
    # Start Flask application
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Starting QuMail Key Manager API")
    print(f"📡 Server: http://localhost:{port}")
    print(f"🔧 Debug mode: {config.DEBUG}")
    print(f"🗄️  Database: {config.NEON_DB_HOST}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=config.DEBUG
    )