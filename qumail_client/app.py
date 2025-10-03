#!/usr/bin/env python3
"""
QuMail - Quantum Secure Email Client
Flask Web Application
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import json
import base64
import tempfile

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import load_config
from qumail_client.embedded_km.neon_key_manager import NeonKeyManager
from qumail_client.crypto.quantum_encryption import QuantumEncryption
from qumail_client.email.email_client import EmailClient
from qumail_client.blockchain.verification import BlockchainVerifier
from qumail_client.ipfs.storage import IPFSStorage

# Load environment variables (but don't override existing environment variables)
load_dotenv(override=False)

# Initialize Flask app
app = Flask(__name__)

# Configuration for production deployment
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'qumail_dev_secret_key_2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///qumail.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Handle Render.com specific database URL format
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Add custom template filter for JSON formatting
@app.template_filter('tojsonpretty')
def tojsonpretty_filter(value):
    """Convert value to pretty JSON string"""
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)
# Configure logging for production
log_handlers = [logging.StreamHandler()]

# Only use file logging if logs directory exists
if os.path.exists('./logs'):
    log_handlers.append(logging.FileHandler('./logs/qumail.log'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# Global components
config = None
key_manager = None
quantum_crypto = None
email_client = None
blockchain_verifier = None
ipfs_storage = None

def initialize_components():
    """Initialize all QuMail components with fallback handling"""
    global config, key_manager, quantum_crypto, email_client, blockchain_verifier, ipfs_storage
    
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize components with individual error handling
        try:
            if config and hasattr(config, 'DATABASE_URL') and config.DATABASE_URL:
                key_manager = NeonKeyManager(config)
                logger.info("Neon Key Manager initialized")
            else:
                logger.warning("Key Manager skipped - no database configuration")
                key_manager = None
        except Exception as e:
            logger.warning(f"Key Manager initialization failed: {e}")
            key_manager = None
        
        try:
            quantum_crypto = QuantumEncryption(config)
            logger.info("Quantum encryption initialized")
        except Exception as e:
            logger.warning(f"Quantum encryption initialization failed: {e}")
            quantum_crypto = None
        
        try:
            email_client = EmailClient(config)
            logger.info("Email client initialized")
        except Exception as e:
            logger.warning(f"Email client initialization failed: {e}")
            email_client = None
        
        # Initialize Blockchain Verifier (optional)
        if hasattr(config, 'ENABLE_BLOCKCHAIN_VERIFICATION') and config.ENABLE_BLOCKCHAIN_VERIFICATION:
            try:
                blockchain_verifier = BlockchainVerifier(config)
                logger.info("Blockchain verifier initialized")
            except Exception as e:
                logger.warning(f"Blockchain verifier initialization failed: {e}")
                blockchain_verifier = None
        
        # Initialize IPFS Storage (optional)
        if hasattr(config, 'ENABLE_IPFS_STORAGE') and config.ENABLE_IPFS_STORAGE:
            try:
                ipfs_storage = IPFSStorage(config)
                logger.info("IPFS storage initialized")
            except Exception as e:
                logger.warning(f"IPFS storage initialization failed: {e}")
                ipfs_storage = None
            
    except Exception as e:
        logger.error(f"Critical configuration error: {e}")
        # Still allow the app to start with minimal functionality
        config = None
    
    return True

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Basic health check
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'environment': os.getenv('FLASK_ENV', 'development')
        }
        
        # Check database connection
        try:
            with app.app_context():
                db.engine.execute("SELECT 1")
            status['database'] = 'connected'
        except Exception as e:
            status['database'] = f'error: {str(e)}'
            status['status'] = 'degraded'
        
        return jsonify(status), 200 if status['status'] == 'healthy' else 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Main dashboard with error handling"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user statistics with fallback values
    stats = {
        'total_keys': 0,
        'active_keys': 0,
        'emails_sent': 0,
        'emails_received': 0
    }
    
    try:
        # Safe key statistics
        if key_manager:
            try:
                user_keys = key_manager.get_user_keys(session['user_id'])
                if user_keys:
                    stats['total_keys'] = len(user_keys)
                    stats['active_keys'] = len([k for k in user_keys if not k.get('expired', False)])
            except Exception as e:
                logger.warning(f"Failed to get user keys: {e}")
        
        # Safe email statistics
        if key_manager:
            try:
                email_stats = key_manager.get_email_statistics(session['user_id'])
                if email_stats:
                    stats.update(email_stats)
            except Exception as e:
                logger.warning(f"Failed to get email statistics: {e}")
                # Use fallback values
                stats.update({
                    'emails_sent': 0,
                    'emails_received': 0
                })
            
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Continue with default stats
    
    return render_template('dashboard.html', stats=stats)

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', 
                         error_title="Internal Server Error",
                         error_message="We apologize for the inconvenience. Please try again or contact support if the problem persists."), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html',
                         error_title="Page Not Found",
                         error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {e}")
    return render_template('error.html',
                         error_title="Something went wrong",
                         error_message="An unexpected error occurred. Please try refreshing the page."), 500

@app.route('/simple-dashboard')
def simple_dashboard():
    """Simple dashboard that works without external dependencies"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stats = {
        'total_keys': 5,  # Placeholder values
        'active_keys': 3,
        'emails_sent': 10,
        'emails_received': 7
    }
    
    return render_template('dashboard.html', stats=stats)

@app.route('/test-dashboard')
def test_dashboard():
    """Test dashboard without any dependencies"""
    # Set a temporary session for testing
    session['user_id'] = 'test@example.com'
    
    stats = {
        'total_keys': 8,
        'active_keys': 6,
        'emails_sent': 15,
        'emails_received': 12
    }
    
    return render_template('dashboard.html', stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with proper authentication"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('login.html')
        
        # Try to authenticate existing user
        auth_result = key_manager.authenticate_user(email, password)
        
        if auth_result['success']:
            session['user_id'] = email
            session['username'] = email.split('@')[0]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(auth_result['error'], 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with OTP verification"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        otp_code = request.form.get('otp_code')
        temp_password_hash = request.form.get('temp_password_hash')
        
        # Step 1: Initial registration (send OTP)
        if email and password and not otp_code:
            if not confirm_password or password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('register.html')
            
            # Create account and send OTP
            result = key_manager.create_user_account(email, password)
            
            if result['success']:
                flash('Verification code sent to your email. Please check and enter the code.', 'info')
                return render_template('register.html', 
                                     step='verify_otp', 
                                     email=email)
            else:
                flash(result['error'], 'error')
        
        # Step 2: OTP verification
        elif email and otp_code:
            result = key_manager.verify_registration_otp(email, otp_code)
            
            if result['success']:
                flash('Registration successful! Please login with your credentials.', 'success')
                return redirect(url_for('login'))
            else:
                flash(result['error'], 'error')
                return render_template('register.html', 
                                     step='verify_otp', 
                                     email=email)
        else:
            flash('Please fill in all required fields', 'error')
    
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        email = request.form.get('email')
        otp_code = request.form.get('otp_code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Step 1: Request password reset
        if email and not otp_code:
            result = key_manager.initiate_password_reset(email)
            
            if result['success']:
                flash('Password reset code sent to your email.', 'info')
                return render_template('forgot_password.html', step='verify_otp', email=email)
            else:
                flash(result['error'], 'error')
        
        # Step 2: Reset password with OTP
        elif email and otp_code and new_password:
            if not confirm_password or new_password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('forgot_password.html', step='verify_otp', email=email)
            
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('forgot_password.html', step='verify_otp', email=email)
            
            result = key_manager.reset_password_with_otp(email, otp_code, new_password)
            
            if result['success']:
                flash('Password reset successful! Please login with your new password.', 'success')
                return redirect(url_for('login'))
            else:
                flash(result['error'], 'error')
                return render_template('forgot_password.html', step='verify_otp', email=email)
        else:
            flash('Please fill in all required fields', 'error')
    
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/compose', methods=['GET', 'POST'])
def compose():
    """Compose new email"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get URL parameters for reply functionality
    reply_to = request.args.get('recipient', '')
    reply_subject = request.args.get('subject', '')
    
    if request.method == 'POST':
        try:
            recipient = request.form.get('recipient')
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            # Generate quantum key for encryption (optimized)
            quantum_key = key_manager.generate_quantum_key(
                user_id=session['user_id'],
                recipient=recipient,
                purpose='email_encryption'
            )
            
            # Share key with recipient (non-blocking)
            try:
                key_manager.share_key_with_recipient(
                    key_id=quantum_key['key_id'],
                    sender_id=session['user_id'],
                    recipient_id=recipient
                )
            except Exception as e:
                logger.warning(f"Key sharing failed: {e}")
            
            # Encrypt message (optimized)
            encrypted_message = quantum_crypto.encrypt_message(message, quantum_key['key_data'])
            
            # Store in IPFS (fast mode - async processing)
            ipfs_hash = None
            blockchain_hash = None
            
            # Skip heavy operations for performance - process later if needed
            # if ipfs_storage:
            #     ipfs_hash = ipfs_storage.store_encrypted_email(...)
            # if blockchain_verifier:
            #     blockchain_hash = blockchain_verifier.verify_email_integrity(...)
            
            # Send email
            email_data = {
                'recipient': recipient,
                'subject': f"[QuMail Secure] {subject}",
                'body': f"Encrypted message (Key ID: {quantum_key['key_id']})\nIPFS: {ipfs_hash}\nBlockchain: {blockchain_hash}",
                'encrypted_content': encrypted_message
            }
            
            success = email_client.send_secure_email(email_data)
            
            if success.get('success'):
                # Record email sent in statistics
                if key_manager:
                    try:
                        # Record for sender (optimized - single database operation)
                        key_manager.record_email_sent(
                            user_id=session['user_id'],
                            recipient=recipient,
                            subject=subject,
                            ipfs_hash=ipfs_hash,
                            encryption_key_id=quantum_key['key_id'],
                            encrypted_content=base64.b64encode(encrypted_message if isinstance(encrypted_message, bytes) else encrypted_message.encode('utf-8')).decode('utf-8')
                        )
                        
                        # Skip recipient recording for performance - they'll see it when they check inbox"
                    except Exception as e:
                        logger.error(f"Failed to record email statistics: {e}")
                
                flash('Secure email sent successfully!', 'success')
            else:
                error_msg = success.get('error', 'Unknown error')
                flash(f'Failed to send email: {error_msg}', 'error')
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            flash(f'Error sending email: {str(e)}', 'error')
        
        return redirect(url_for('compose'))
    
    return render_template('compose.html', reply_to=reply_to, reply_subject=reply_subject)

@app.route('/inbox')
def inbox():
    """View inbox with sent and received emails"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    all_emails = []
    sent_count = 0
    received_count = 0
    
    try:
        if key_manager:
            # Get emails with optimized query (limit to recent 50 emails)
            all_user_emails = key_manager.get_user_inbox(session['user_id'])
            
            # Process emails efficiently
            for email in all_user_emails[:50]:  # Limit to 50 most recent
                all_emails.append({
                    'id': email.get('id', ''),
                    'type': email.get('type', ''),
                    'sender': email.get('sender', ''),
                    'recipient': email.get('recipient', ''),
                    'subject': email.get('subject', ''),
                    'timestamp': email.get('timestamp', ''),
                    'encrypted': True,
                    'key_id': email.get('encryption_key_id', ''),
                    'has_documents': bool(email.get('ipfs_hash'))
                })
                
                # Count by type
                if email.get('type') == 'sent':
                    sent_count += 1
                elif email.get('type') == 'received':
                    received_count += 1
            
            # Already sorted by database query (newest first)
            
    except Exception as e:
        logger.error(f"Failed to get emails: {e}")
        flash(f'Error loading emails: {str(e)}', 'error')
    
    return render_template('inbox.html', 
                         emails=all_emails, 
                         sent_count=sent_count, 
                         received_count=received_count)

@app.route('/view_email/<int:email_id>')
def view_email(email_id):
    """View email content and documents from IPFS"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    email_data = None
    decrypted_content = None
    ipfs_document = None
    
    try:
        if key_manager:
            # Get email from both sent and received
            sent_emails = key_manager.get_sent_emails(session['user_id'])
            received_emails = key_manager.get_received_emails(session['user_id'])
            
            logger.info(f"Looking for email {email_id} among {len(sent_emails)} sent and {len(received_emails)} received emails")
            
            # Find the email and mark its type
            for email in sent_emails:
                if email.get('id') == email_id:
                    email_data = email
                    email_data['type'] = 'sent'
                    email_data['sender'] = session['user_id']  # Sender is current user
                    logger.info(f"Found SENT email {email_id}: {email.get('subject')}")
                    break
            
            # If not found in sent, check received
            if not email_data:
                for email in received_emails:
                    if email.get('id') == email_id:
                        email_data = email
                        email_data['type'] = 'received'
                        # sender field should already be set from database
                        logger.info(f"Found RECEIVED email {email_id}: {email.get('subject')}")
                        break
            
            if not email_data:
                flash('Email not found', 'error')
                return redirect(url_for('inbox'))
            
            # Try to decrypt content if available
            if email_data.get('content') or email_data.get('encrypted_content'):
                try:
                    # Get encrypted content from either field
                    encrypted_content = email_data.get('content') or email_data.get('encrypted_content')
                    key_id = email_data.get('key_id') or email_data.get('encryption_key_id')
                    
                    logger.info(f"Attempting decryption - Key ID: {key_id}")
                    logger.info(f"Encrypted content length: {len(encrypted_content) if encrypted_content else 0}")
                    logger.info(f"Encrypted content type: {type(encrypted_content)}")
                    logger.info(f"Encrypted content preview: {encrypted_content[:50] if encrypted_content else 'None'}...")
                    
                    if key_id:
                        # Get decryption key - include expired keys to handle old emails
                        user_keys = key_manager.get_user_keys(session['user_id'], include_expired=True)
                        decryption_key = None
                        
                        logger.info(f"Found {len(user_keys)} total keys for user {session['user_id']}")
                        logger.info(f"Looking for key_id: '{key_id}'")
                        
                        # Log all available keys for debugging
                        for i, key in enumerate(user_keys):
                            logger.info(f"Key {i+1}: ID='{key.get('key_id')}', Purpose={key.get('purpose')}, Expired={key.get('expired')}")
                        
                        for key in user_keys:
                            if key.get('key_id') == key_id:
                                decryption_key = key.get('key_data')
                                logger.info(f"✓ Found matching key: {key_id}")
                                logger.info(f"Key data type: {type(decryption_key)}, Length: {len(decryption_key) if decryption_key else 0}")
                                break
                        
                        if decryption_key:
                            # Ensure decryption key is bytes
                            if isinstance(decryption_key, str):
                                try:
                                    decryption_key = base64.b64decode(decryption_key)
                                    logger.info("Converted key from base64 string to bytes")
                                except Exception as e:
                                    logger.warning(f"Base64 decode of key failed: {e}, trying UTF-8 encode")
                                    decryption_key = decryption_key.encode('utf-8')
                            
                            # Try multiple decryption approaches
                            decryption_successful = False
                            
                            # Method 1: Base64 decode + decrypt (most common)
                            try:
                                logger.info("Trying Method 1: Base64 decode + decrypt")
                                encrypted_bytes = base64.b64decode(encrypted_content) if isinstance(encrypted_content, str) else encrypted_content
                                logger.info(f"Decoded to {len(encrypted_bytes)} bytes")
                                decrypted_content = quantum_crypto.decrypt_message(encrypted_bytes, decryption_key)
                                if isinstance(decrypted_content, bytes):
                                    decrypted_content = decrypted_content.decode('utf-8')
                                logger.info(f"✓ Successfully decrypted using Method 1 (base64)")
                                decryption_successful = True
                            except Exception as e:
                                logger.warning(f"Method 1 failed: {e}")
                            
                            # Method 2: Direct decrypt (already bytes)
                            if not decryption_successful:
                                try:
                                    logger.info("Trying Method 2: Direct decrypt")
                                    encrypted_bytes = encrypted_content if isinstance(encrypted_content, bytes) else encrypted_content.encode('utf-8')
                                    decrypted_content = quantum_crypto.decrypt_message(encrypted_bytes, decryption_key)
                                    if isinstance(decrypted_content, bytes):
                                        decrypted_content = decrypted_content.decode('utf-8')
                                    logger.info(f"✓ Successfully decrypted using Method 2 (direct)")
                                    decryption_successful = True
                                except Exception as e:
                                    logger.warning(f"Method 2 failed: {e}")
                            
                            # Method 3: Hex decode + decrypt
                            if not decryption_successful:
                                try:
                                    logger.info("Trying Method 3: Hex decode + decrypt")
                                    encrypted_bytes = bytes.fromhex(encrypted_content) if isinstance(encrypted_content, str) else encrypted_content
                                    decrypted_content = quantum_crypto.decrypt_message(encrypted_bytes, decryption_key)
                                    if isinstance(decrypted_content, bytes):
                                        decrypted_content = decrypted_content.decode('utf-8')
                                    logger.info(f"✓ Successfully decrypted using Method 3 (hex)")
                                    decryption_successful = True
                                except Exception as e:
                                    logger.warning(f"Method 3 failed: {e}")
                            
                            if not decryption_successful:
                                logger.error("All decryption methods failed!")
                                decrypted_content = "Content is encrypted - all decryption methods failed"
                        else:
                            logger.error(f"✗ Decryption key {key_id} not found among {len(user_keys)} keys")
                            decrypted_content = "Content is encrypted - decryption key not found or invalid"
                    else:
                        logger.error("✗ No key_id found for this email")
                        decrypted_content = "Content is encrypted - no encryption key ID available"
                        
                except Exception as e:
                    logger.error(f"Failed to decrypt email content: {e}")
                    decrypted_content = f"Content is encrypted - decryption failed: {str(e)}"
            
            # Retrieve IPFS document if available
            if email_data.get('ipfs_hash') and ipfs_storage:
                try:
                    ipfs_document = ipfs_storage.retrieve_email(email_data['ipfs_hash'])
                except Exception as e:
                    logger.error(f"Failed to retrieve IPFS document: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to view email {email_id}: {e}")
        flash(f'Error loading email: {str(e)}', 'error')
        return redirect(url_for('inbox'))
    
    return render_template('view_email.html', 
                         email=email_data,
                         decrypted_content=decrypted_content,
                         ipfs_document=ipfs_document)

@app.route('/keys')
def keys():
    """Manage quantum keys"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_keys = []
    try:
        if key_manager:
            user_keys = key_manager.get_user_keys(session['user_id'])
    except Exception as e:
        logger.error(f"Failed to get user keys: {e}")
        flash(f'Error loading keys: {str(e)}', 'error')
    
    return render_template('keys.html', keys=user_keys)

@app.route('/api/generate_key', methods=['POST'])
def api_generate_key():
    """API endpoint to generate new quantum key"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        recipient = data.get('recipient', 'general_use')
        purpose = data.get('purpose', 'manual_generation')
        
        quantum_key = key_manager.generate_quantum_key(
            user_id=session['user_id'],
            recipient=recipient,
            purpose=purpose
        )
        
        return jsonify({
            'success': True,
            'key_id': quantum_key['key_id'],
            'key_length': len(quantum_key['key_data']),
            'created_at': quantum_key['created_at'],
            'expires_at': quantum_key['expires_at']
        })
        
    except Exception as e:
        logger.error(f"Failed to generate key: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_key/<key_id>', methods=['DELETE'])
def api_delete_key(key_id):
    """API endpoint to delete a quantum key"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        success = key_manager.delete_key(key_id, session['user_id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Key not found or access denied'}), 404
            
    except Exception as e:
        logger.error(f"Failed to delete key: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_status')
def system_status():
    """Get system status"""
    status = {
        'quantum_encryption': False,
        'blockchain_verification': False,
        'ipfs_storage': False,
        'key_manager': False,
        'database_connected': False,
        'email_client': False
    }
    
    # Test Quantum Encryption
    try:
        if quantum_crypto:
            # Test encryption functionality
            test_result = quantum_crypto.test_encryption()
            status['quantum_encryption'] = test_result
    except Exception as e:
        logger.error(f"Quantum crypto test failed: {e}")
        status['quantum_encryption'] = False
    
    # Test Blockchain Verification
    try:
        if blockchain_verifier:
            # Test blockchain connection
            test_result = blockchain_verifier.test_connection()
            status['blockchain_verification'] = test_result.get('success', False)
    except Exception as e:
        logger.error(f"Blockchain test failed: {e}")
        status['blockchain_verification'] = False
    
    # Test IPFS Storage
    try:
        if ipfs_storage:
            # Test IPFS connection
            test_result = ipfs_storage.test_connection()
            status['ipfs_storage'] = test_result.get('success', False)
    except Exception as e:
        logger.error(f"IPFS test failed: {e}")
        status['ipfs_storage'] = False
    
    # Test Key Manager
    try:
        if key_manager:
            key_manager.test_connection()
            status['key_manager'] = True
    except Exception as e:
        logger.error(f"Key manager test failed: {e}")
        status['key_manager'] = False
    
    # Test Database Connection
    try:
        if key_manager:
            key_manager.test_connection()
            status['database_connected'] = True
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        status['database_connected'] = False
    
    # Test Email Client
    try:
        if email_client:
            # Email client is always available (demo mode or real)
            status['email_client'] = True
    except Exception as e:
        logger.error(f"Email client test failed: {e}")
        status['email_client'] = False
    
    return jsonify(status)

@app.route('/api/send_email', methods=['POST'])
def send_email():
    """Send secure email with optional file attachments"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Handle both JSON and form data
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            files = []
        else:
            # Form data with possible file uploads
            data = request.form.to_dict()
            files = request.files.getlist('attachments')
        
        sender = session['user_id']  # Always use logged-in user as sender
        recipient = data.get('recipient')
        subject = data.get('subject')
        content = data.get('content')
        encryption_key = data.get('encryption_key', 'auto')
        priority = data.get('priority', 'normal')
        
        if not all([recipient, subject, content]):
            return jsonify({'success': False, 'error': 'Missing required fields: recipient, subject, content'}), 400
        
        # Handle file attachments and prepare for IPFS storage
        attachment_files = []
        attachment_paths = []
        if files:
            import tempfile
            import os
            import time
            for file in files:
                if file.filename and file.filename.strip():
                    try:
                        # Read file data once
                        file_data = file.read()
                        logger.info(f"Read attachment: {file.filename} ({len(file_data)} bytes)")
                        
                        # Add to IPFS attachment list
                        attachment_files.append({
                            'data': file_data,
                            'filename': file.filename,
                            'content_type': file.content_type or 'application/octet-stream'
                        })
                        
                        # Also save temporarily for email sending (backup)
                        temp_dir = tempfile.gettempdir()
                        # Ensure temp directory exists
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # Sanitize filename to avoid path issues
                        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in '._-').strip()
                        if not safe_filename:
                            safe_filename = f"attachment_{int(time.time())}"
                        
                        temp_path = os.path.join(temp_dir, f"qumail_attachment_{safe_filename}")
                        
                        # Write file data to temp file
                        with open(temp_path, 'wb') as temp_file:
                            temp_file.write(file_data)
                        
                        attachment_paths.append(temp_path)
                        logger.info(f"Prepared attachment for IPFS and email: {file.filename} -> {temp_path}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process attachment {file.filename}: {e}")
                        continue

        # Generate or use existing key for encryption
        key_result = None
        if encryption_key == 'auto':
            # Generate new key for this email
            try:
                key_result = key_manager.generate_quantum_key(
                    user_id=sender,
                    recipient=recipient,
                    purpose='email_encryption'
                )
                encryption_key_id = key_result['key_id']
                
                # **CRITICAL**: Share the key with the recipient so they can decrypt
                try:
                    key_manager.share_key_with_recipient(
                        key_id=encryption_key_id,
                        sender_id=sender,
                        recipient_id=recipient
                    )
                    logger.info(f"Shared decryption key {encryption_key_id} with recipient {recipient}")
                except Exception as e:
                    logger.error(f"Failed to share key with recipient: {e}")
                    # Continue anyway - sender can still decrypt
                    
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to generate encryption key: {str(e)}'}), 500
        else:
            encryption_key_id = encryption_key
            # Get existing key data
            try:
                key_result = key_manager.get_key(encryption_key_id)
                if not key_result:
                    return jsonify({'success': False, 'error': 'Specified encryption key not found'}), 400
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to retrieve encryption key: {str(e)}'}), 500
        
        # Encrypt content using quantum encryption
        encrypted_content = quantum_crypto.encrypt_message(content, key_result['key_data'])
        
        # Store email with attachments on IPFS
        email_data = {
            'sender': sender,
            'recipient': recipient,
            'subject': subject,
            'encrypted_content': encrypted_content.hex(),
            'encryption_key_id': encryption_key_id,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store attachments and email separately
        if attachment_files:
            logger.info(f"Storing {len(attachment_files)} attachments on IPFS")
            # Use new method that handles attachments
            ipfs_result = ipfs_storage.store_email_with_attachments(email_data, attachment_files)
        else:
            # No attachments, store email only
            ipfs_result = ipfs_storage.store_email(email_data)
            ipfs_result = {'success': ipfs_result['success'], 'email_hash': ipfs_result.get('hash'), 'attachments': []}
        
        if not ipfs_result['success']:
            return jsonify({'success': False, 'error': 'Failed to store email on IPFS'}), 500
        
        ipfs_hash = ipfs_result['email_hash']
        attachments_info = ipfs_result.get('attachments', [])
        
        logger.info(f"Email stored on IPFS: {ipfs_hash}")
        if attachments_info:
            logger.info(f"Attachments stored: {[att['filename'] for att in attachments_info]}")
        
        # Verify on blockchain
        verification_result = blockchain_verifier.verify_email_integrity(ipfs_hash, encrypted_content)
        
        # Send actual email
        email_send_result = email_client.send_secure_email({
            'sender': sender,  # Pass the actual sender
            'recipient': recipient,
            'subject': f"[QuMail Secure] {subject}",
            'encrypted_content': encrypted_content,
            'attachments': attachment_paths  # File paths for email sending
        })
        
        if email_send_result.get('success'):
            logger.info(f"Secure email sent from {sender} to {recipient}")
            
            # Record email statistics for BOTH sender and recipient
            try:
                # Record for sender (existing logic)
                key_manager.record_email_sent(
                    user_id=sender,
                    recipient=recipient,
                    subject=subject,
                    ipfs_hash=ipfs_hash,
                    encryption_key_id=encryption_key_id,
                    encrypted_content=base64.b64encode(encrypted_content if isinstance(encrypted_content, bytes) else encrypted_content.encode('utf-8')).decode('utf-8')
                )
                
                # NEW: Record for recipient as a received email
                key_manager.record_email_received(
                    user_id=recipient,
                    sender=sender,
                    subject=subject,
                    ipfs_hash=ipfs_hash,
                    encryption_key_id=encryption_key_id,
                    encrypted_content=base64.b64encode(encrypted_content if isinstance(encrypted_content, bytes) else encrypted_content.encode('utf-8')).decode('utf-8')
                )
                
                logger.info(f"Email recorded for both sender ({sender}) and recipient ({recipient})")
                
            except Exception as e:
                logger.warning(f"Failed to record email statistics: {e}")
            
            # Clean up temporary attachment files
            for temp_path in attachment_paths:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        logger.info(f"Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")
            
            return jsonify({
                'success': True, 
                'message': 'Email sent successfully',
                'ipfs_hash': ipfs_hash,
                'encryption_key_id': encryption_key_id,
                'blockchain_verified': verification_result.get('success', False),
                'attachments_count': len(attachment_paths)
            })
        else:
            # Clean up temporary files even if send failed
            for temp_path in attachment_paths:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception:
                    pass
            return jsonify({
                'success': False, 
                'error': f"Failed to send email: {email_send_result.get('error', 'Unknown error')}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/email/<email_id>')
def get_email(email_id):
    """Get email details with decryption"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get email from database
        if not key_manager:
            return jsonify({'success': False, 'error': 'Key manager not available'}), 500
            
        sent_emails = key_manager.get_sent_emails(session['user_id'])
        email_data = None
        
        # Find the specific email
        for email in sent_emails:
            if str(email.get('id', '')) == str(email_id):
                email_data = email
                break
        
        if not email_data:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        # Try to get encrypted content from IPFS first, fallback to database
        decrypted_content = "Unable to decrypt content"
        encrypted_content = None
        
        # First try IPFS
        if email_data.get('ipfs_hash') and ipfs_storage:
            try:
                ipfs_result = ipfs_storage.retrieve_email(email_data['ipfs_hash'])
                if ipfs_result.get('success'):
                    stored_email_data = ipfs_result.get('data', {})
                    encrypted_content = stored_email_data.get('encrypted_content', '')
                    logger.info("Successfully retrieved content from IPFS")
                else:
                    logger.warning(f"IPFS retrieval failed: {ipfs_result.get('error', 'Unknown error')}")
            except Exception as ipfs_error:
                logger.warning(f"IPFS retrieval error: {ipfs_error}")
        
        # Fallback to database if IPFS failed
        if not encrypted_content and email_data.get('encrypted_content'):
            encrypted_content = email_data.get('encrypted_content')
            logger.info("Using encrypted content from database as fallback")
        
        # Decrypt content if we have it
        if encrypted_content and quantum_crypto and email_data.get('encryption_key_id'):
            try:
                # Get the quantum key used for encryption - include expired keys
                user_keys = key_manager.get_user_keys(session['user_id'], include_expired=True)
                encryption_key_data = None
                
                logger.info(f"Looking for encryption key: {email_data.get('encryption_key_id')}")
                logger.info(f"User has {len(user_keys)} keys available")
                
                for key in user_keys:
                    if key.get('key_id') == email_data.get('encryption_key_id'):
                        encryption_key_data = key.get('key_data')
                        logger.info("Found matching encryption key!")
                        break
                
                if encryption_key_data:
                    # Ensure key is bytes
                    if isinstance(encryption_key_data, str):
                        try:
                            encryption_key_data = base64.b64decode(encryption_key_data)
                        except:
                            encryption_key_data = encryption_key_data.encode('utf-8')
                    
                    # Try multiple decryption methods
                    decryption_methods = [
                        # Method 1: Base64 decode + decrypt
                        lambda: quantum_crypto.decrypt_message(
                            base64.b64decode(encrypted_content) if isinstance(encrypted_content, str) else encrypted_content,
                            encryption_key_data
                        ),
                        # Method 2: Direct decrypt
                        lambda: quantum_crypto.decrypt_message(
                            encrypted_content if isinstance(encrypted_content, bytes) else encrypted_content.encode('utf-8'),
                            encryption_key_data
                        ),
                        # Method 3: Hex decode + decrypt
                        lambda: quantum_crypto.decrypt_message(
                            bytes.fromhex(encrypted_content) if isinstance(encrypted_content, str) else encrypted_content,
                            encryption_key_data
                        )
                    ]
                    
                    decryption_successful = False
                    for i, method in enumerate(decryption_methods):
                        try:
                            decrypted_content = method()
                            if isinstance(decrypted_content, bytes):
                                decrypted_content = decrypted_content.decode('utf-8')
                            logger.info(f"Successfully decrypted using method {i+1}")
                            decryption_successful = True
                            break
                        except Exception as e:
                            pass  # Skip logging for performance
                            continue
                    
                    if not decryption_successful:
                        decrypted_content = "Content is encrypted - all decryption methods failed"
                        
                else:
                    logger.error(f"Encryption key {email_data.get('encryption_key_id')} not found")
                    decrypted_content = "Content is encrypted - decryption key not found"
                    
            except Exception as decrypt_error:
                logger.error(f"Failed to decrypt email content: {decrypt_error}")
                decrypted_content = f"Content is encrypted - decryption error: {str(decrypt_error)}"
        elif not encrypted_content:
            decrypted_content = "No content available"
        elif not quantum_crypto:
            decrypted_content = "Quantum crypto system not available"
        elif not email_data.get('encryption_key_id'):
            decrypted_content = "No encryption key ID available"
        else:
            decrypted_content = "Unknown decryption issue"
        
        response_data = {
            'id': email_data.get('id', ''),
            'sender': session['user_id'],
            'recipient': email_data.get('recipient', ''),
            'subject': email_data.get('subject', ''),
            'content': decrypted_content,
            'timestamp': email_data.get('sent_at', ''),
            'encrypted': True,
            'key_id': email_data.get('encryption_key_id', ''),
            'ipfs_hash': email_data.get('ipfs_hash', '')
        }
        
        return jsonify({'success': True, 'email': response_data})
        
    except Exception as e:
        logger.error(f"Error getting email: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/email/<email_id>', methods=['DELETE'])
def delete_email(email_id):
    """Delete email"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        if not key_manager:
            return jsonify({'success': False, 'error': 'Key manager not available'}), 500
        
        # Delete email from database
        success = key_manager.delete_email(email_id, session['user_id'])
        
        if success:
            logger.info(f"Email {email_id} deleted by user {session['user_id']}")
            return jsonify({'success': True, 'message': 'Email deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Email not found or access denied'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting email: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/emails/delete', methods=['POST'])
def delete_multiple_emails():
    """Delete multiple emails"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        if not key_manager:
            return jsonify({'success': False, 'error': 'Key manager not available'}), 500
        
        data = request.get_json()
        email_ids = data.get('email_ids', [])
        
        if not email_ids:
            return jsonify({'success': False, 'error': 'No email IDs provided'}), 400
        
        # Delete emails from database
        deleted_count = 0
        for email_id in email_ids:
            try:
                if key_manager.delete_email(email_id, session['user_id']):
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete email {email_id}: {e}")
        
        logger.info(f"Deleted {deleted_count}/{len(email_ids)} emails for user {session['user_id']}")
        return jsonify({
            'success': True, 
            'message': f'Deleted {deleted_count} of {len(email_ids)} emails',
            'deleted_count': deleted_count,
            'total_requested': len(email_ids)
        })
        
    except Exception as e:
        logger.error(f"Error deleting emails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/key/<key_id>')
def get_key_details(key_id):
    """Get key details"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get key details from key manager
        user_email = session['user_id']
        keys = key_manager.get_user_keys(user_email)
        
        key_details = None
        for key in keys:
            if key['key_id'] == key_id:
                key_details = key
                break
        
        if not key_details:
            return jsonify({'success': False, 'error': 'Key not found'}), 404
        
        return jsonify({'success': True, 'key': key_details})
        
    except Exception as e:
        logger.error(f"Error getting key details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/key/<key_id>', methods=['DELETE'])
def delete_key_endpoint(key_id):
    """Delete a specific key"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        user_email = session['user_id']
        result = key_manager.delete_key(key_id, user_email)
        
        if result['success']:
            logger.info(f"Key {key_id} deleted by {user_email}")
            return jsonify({'success': True, 'message': 'Key deleted successfully'})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to delete key')}), 500
        
    except Exception as e:
        logger.error(f"Error deleting key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Debug API endpoints removed for production performance

@app.route('/api/debug/list_keys')
def debug_list_keys():
    """Debug endpoint to list all keys"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get all keys including expired
        keys = key_manager.get_user_keys(session['user_id'], include_expired=True)
        
        # Remove sensitive key_data from response
        safe_keys = []
        for key in keys:
            safe_key = {k: v for k, v in key.items() if k != 'key_data'}
            safe_keys.append(safe_key)
        
        return jsonify({
            'success': True,
            'keys': safe_keys,
            'total': len(safe_keys)
        })
        
    except Exception as e:
        logger.error(f"Failed to list keys: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug/manual_decrypt', methods=['POST'])
def debug_manual_decrypt():
    """Debug endpoint to manually test decryption"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        encrypted_content = data.get('encrypted_content')
        key_id = data.get('key_id')
        
        if not encrypted_content or not key_id:
            return jsonify({'success': False, 'error': 'Missing encrypted_content or key_id'}), 400
        
        # Get the key
        user_keys = key_manager.get_user_keys(session['user_id'], include_expired=True)
        decryption_key = None
        
        for key in user_keys:
            if key.get('key_id') == key_id:
                decryption_key = key.get('key_data')
                break
        
        if not decryption_key:
            return jsonify({
                'success': False, 
                'error': f'Key {key_id} not found',
                'details': f'Available keys: {[k.get("key_id") for k in user_keys]}'
            }), 404
        
        # Ensure key is bytes
        if isinstance(decryption_key, str):
            try:
                decryption_key = base64.b64decode(decryption_key)
            except:
                decryption_key = decryption_key.encode('utf-8')
        
        # Try decryption methods
        methods = [
            ('base64', lambda: quantum_crypto.decrypt_message(base64.b64decode(encrypted_content), decryption_key)),
            ('direct', lambda: quantum_crypto.decrypt_message(encrypted_content.encode('utf-8'), decryption_key)),
            ('hex', lambda: quantum_crypto.decrypt_message(bytes.fromhex(encrypted_content), decryption_key))
        ]
        
        for method_name, method in methods:
            try:
                decrypted = method()
                if isinstance(decrypted, bytes):
                    decrypted = decrypted.decode('utf-8')
                return jsonify({
                    'success': True,
                    'decrypted_content': decrypted,
                    'method_used': method_name
                })
            except Exception as e:
                logger.debug(f"Method {method_name} failed: {e}")
                continue
        
        return jsonify({
            'success': False,
            'error': 'All decryption methods failed',
            'details': 'Tried base64, direct, and hex decoding'
        }), 500
        
    except Exception as e:
        logger.error(f"Manual decrypt failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/fix_old_emails', methods=['POST'])
def fix_old_emails():
    """Fix old emails by sharing keys with recipients"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        user_email = session['user_id']
        
        # Get all sent emails for this user
        sent_emails = key_manager.get_sent_emails(user_email, limit=100)
        
        success_count = 0
        fail_count = 0
        already_shared_count = 0
        
        for email in sent_emails:
            key_id = email.get('encryption_key_id') or email.get('key_id')
            recipient = email.get('recipient')
            
            if not key_id or not recipient:
                fail_count += 1
                continue
            
            try:
                # Try to share the key
                result = key_manager.share_key_with_recipient(key_id, user_email, recipient)
                if result:
                    success_count += 1
                else:
                    already_shared_count += 1
            except Exception as e:
                if "duplicate key value" in str(e).lower():
                    already_shared_count += 1
                else:
                    fail_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(sent_emails)} emails',
            'shared': success_count,
            'already_shared': already_shared_count,
            'failed': fail_count,
            'total': len(sent_emails)
        })
        
    except Exception as e:
        logger.error(f"Failed to fix old emails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Debug functionality removed for production performance

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return '', 204

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """Serve apple touch icon"""
    return '', 204

@app.route('/apple-touch-icon-precomposed.png')
def apple_touch_icon_precomposed():
    """Serve apple touch icon precomposed"""
    return '', 204

@app.route('/settings')
def settings():
    """Application settings"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('settings.html', config=config)

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

def create_directories():
    """Create necessary directories"""
    directories = ['./logs', './temp/qumail']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """Main application entry point"""
    try:
        # Create necessary directories
        create_directories()
        
        # Initialize components (non-blocking)
        initialize_components()
        logger.info("Component initialization completed")
        
        # Get Flask configuration from environment
        # For cloud deployment (like Render), use 0.0.0.0 and PORT env var
        port = int(os.getenv('PORT', 10000))  # Render sets PORT, fallback to 10000
        
        # For production deployment (Render), always bind to 0.0.0.0
        # Override any local HOST setting for production
        if os.getenv('FLASK_ENV') == 'production' or os.getenv('PORT'):  # Render sets PORT
            host = '0.0.0.0'
        else:
            host = os.getenv('HOST', '127.0.0.1')  # Local development
        
        # Force disable debug for performance
        debug = False
        
        logger.info(f"Starting QuMail Flask application on {host}:{port}")
        logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        logger.info(f"Debug mode: {debug}")
        
        # Create database tables if they don't exist
        try:
            with app.app_context():
                db.create_all()
                logger.info("Database tables created/verified")
        except Exception as e:
            logger.warning(f"Database table creation failed: {e}")
        
        # Run Flask application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start QuMail application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()