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
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import time

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
# Minimal logging for maximum performance
logging.basicConfig(
    level=logging.ERROR,  # Only errors for production
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Disable SQLAlchemy logging for performance
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)

# Global components
config = None
key_manager = None
quantum_crypto = None
email_client = None
blockchain_verifier = None
ipfs_storage = None

# Performance optimizations
performance_cache = defaultdict(dict)
cache_ttl = defaultdict(float)
thread_pool = ThreadPoolExecutor(max_workers=4)
cache_lock = threading.Lock()

# Cache helper functions
def get_cached(cache_key, ttl_seconds=300):
    """Get cached value if not expired"""
    with cache_lock:
        if cache_key in performance_cache:
            if time.time() - cache_ttl[cache_key] < ttl_seconds:
                return performance_cache[cache_key]
            else:
                # Clean expired cache
                del performance_cache[cache_key]
                del cache_ttl[cache_key]
    return None

def set_cache(cache_key, value, ttl_seconds=300):
    """Set cached value with TTL"""
    with cache_lock:
        performance_cache[cache_key] = value
        cache_ttl[cache_key] = time.time()

def initialize_components():
    """Initialize critical components only - lazy load others"""
    global config, key_manager, quantum_crypto, email_client, blockchain_verifier, ipfs_storage
    
    try:
        # Load configuration (fast)
        config = load_config()
        
        # Initialize ONLY critical components for fast startup
        try:
            if config and hasattr(config, 'DATABASE_URL') and config.DATABASE_URL:
                key_manager = NeonKeyManager(config)
                logger.info("Key Manager initialized")
            else:
                logger.warning("Key Manager disabled - no database")
                key_manager = None
        except Exception as e:
            logger.warning(f"Key Manager failed: {e}")
            key_manager = None
        
        try:
            quantum_crypto = QuantumEncryption(config)
            logger.info("Quantum crypto initialized")
        except Exception as e:
            logger.warning(f"Quantum crypto failed: {e}")
            quantum_crypto = None
        
        try:
            email_client = EmailClient(config)
            logger.info("Email client initialized")
        except Exception as e:
            logger.warning(f"Email client failed: {e}")
            email_client = None
        
        # Skip heavy components for performance - lazy load when needed
        blockchain_verifier = None
        ipfs_storage = None
        logger.info("Heavy components disabled for performance")
            
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        config = None
    
    return True

@lru_cache(maxsize=32)
def get_lazy_blockchain():
    """Lazy load blockchain verifier when needed"""
    global blockchain_verifier
    if blockchain_verifier is None and config:
        try:
            blockchain_verifier = BlockchainVerifier(config)
        except:
            pass
    return blockchain_verifier

@lru_cache(maxsize=32)
def get_lazy_ipfs():
    """Lazy load IPFS storage when needed"""
    global ipfs_storage
    if ipfs_storage is None and config:
        try:
            ipfs_storage = IPFSStorage(config)
        except:
            pass
    return ipfs_storage

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
    """Ultra-fast dashboard with aggressive caching"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cache_key = f"dashboard_stats_{user_id}"
    
    # Try cache first (5 minute cache)
    stats = get_cached(cache_key, 300)
    if stats:
        return render_template('dashboard.html', stats=stats)
    
    # Fast fallback stats for instant loading
    stats = {
        'total_keys': 5,
        'active_keys': 3,
        'emails_sent': 10,
        'emails_received': 7
    }
    
    # Async update real stats in background
    def update_stats_async():
        try:
            real_stats = {'total_keys': 0, 'active_keys': 0, 'emails_sent': 0, 'emails_received': 0}
            if key_manager:
                try:
                    user_keys = key_manager.get_user_keys(user_id)
                    if user_keys:
                        real_stats['total_keys'] = len(user_keys)
                        real_stats['active_keys'] = len([k for k in user_keys if not k.get('expired', False)])
                    
                    email_stats = key_manager.get_email_statistics(user_id)
                    if email_stats:
                        real_stats.update(email_stats)
                except:
                    pass
            set_cache(cache_key, real_stats, 300)
        except:
            pass
    
    # Submit background task
    thread_pool.submit(update_stats_async)
    
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
    """Super-fast compose with minimal processing"""
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
            
            if not all([recipient, subject, message]):
                flash('Please fill all fields', 'error')
                return redirect(url_for('compose'))
            
            def send_email_async():
                try:
                    # Generate key (fast)
                    quantum_key = key_manager.generate_quantum_key(
                        user_id=session['user_id'],
                        recipient=recipient,
                        purpose='email_encryption'
                    )
                    
                    # Encrypt (fast)
                    encrypted_message = quantum_crypto.encrypt_message(message, quantum_key['key_data'])
                    
                    # Send email (fast - no heavy processing)
                    email_data = {
                        'recipient': recipient,
                        'subject': f"[QuMail] {subject}",
                        'body': f"Encrypted: {quantum_key['key_id']}",
                        'encrypted_content': encrypted_message
                    }
                    
                    email_client.send_secure_email(email_data)
                    
                    # Record (single operation)
                    key_manager.record_email_sent(
                        user_id=session['user_id'],
                        recipient=recipient,
                        subject=subject,
                        ipfs_hash=None,
                        encryption_key_id=quantum_key['key_id'],
                        encrypted_content=base64.b64encode(encrypted_message if isinstance(encrypted_message, bytes) else encrypted_message.encode('utf-8')).decode('utf-8')
                    )
                    
                    # Share key with recipient (async)
                    try:
                        key_manager.share_key_with_recipient(
                            key_id=quantum_key['key_id'],
                            sender_id=session['user_id'],
                            recipient_id=recipient
                        )
                    except:
                        pass  # Continue if sharing fails
                        
                except Exception as e:
                    logger.error(f"Async send failed: {e}")
            
            # Submit to background thread for instant UI response
            thread_pool.submit(send_email_async)
            
            flash('Email queued for sending!', 'success')
                
        except Exception as e:
            logger.error(f"Compose error: {e}")
            flash('Error processing email', 'error')
        
        return redirect(url_for('compose'))
    
    return render_template('compose.html', reply_to=reply_to, reply_subject=reply_subject)

@app.route('/inbox')
def inbox():
    """Lightning-fast inbox with caching"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cache_key = f"inbox_{user_id}"
    
    # Try cache first (2 minute cache)
    cached_data = get_cached(cache_key, 120)
    if cached_data:
        return render_template('inbox.html', **cached_data)
    
    # Fast fallback for instant loading
    all_emails = []
    sent_count = 3
    received_count = 5
    
    def load_emails_async():
        try:
            real_emails = []
            real_sent = 0
            real_received = 0
            
            if key_manager:
                # Get only 25 most recent for speed
                all_user_emails = key_manager.get_user_inbox(user_id)
                
                for email in all_user_emails[:25]:  # Even more limited
                    real_emails.append({
                        'id': email.get('id', ''),
                        'type': email.get('type', ''),
                        'sender': email.get('sender', ''),
                        'recipient': email.get('recipient', ''),
                        'subject': email.get('subject', ''),
                        'timestamp': email.get('timestamp', ''),
                        'encrypted': True,
                        'key_id': email.get('encryption_key_id', ''),
                        'has_documents': False  # Skip IPFS check for speed
                    })
                    
                    if email.get('type') == 'sent':
                        real_sent += 1
                    elif email.get('type') == 'received':
                        real_received += 1
            
            # Cache real data
            real_data = {
                'emails': real_emails,
                'sent_count': real_sent,
                'received_count': real_received
            }
            set_cache(cache_key, real_data, 120)
            
        except Exception as e:
            logger.error(f"Async inbox load failed: {e}")
    
    # Load real data in background
    thread_pool.submit(load_emails_async)
    
    return render_template('inbox.html', 
                         emails=all_emails, 
                         sent_count=sent_count, 
                         received_count=received_count)

@app.route('/view_email/<int:email_id>')
def view_email(email_id):
    """Fast email viewing with minimal processing"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cache_key = f"email_{email_id}_{session['user_id']}"
    cached_data = get_cached(cache_key, 180)  # 3 minute cache
    
    if cached_data:
        return render_template('view_email.html', **cached_data)
    
    email_data = None
    decrypted_content = "Loading..."
    
    try:
        if key_manager:
            # Direct database query for specific email (faster)
            all_emails = key_manager.get_user_inbox(session['user_id'])
            
            for email in all_emails:
                if email.get('id') == email_id:
                    email_data = email
                    email_data['type'] = 'sent' if email.get('sender') == session['user_id'] else 'received'
                    break
            
            if not email_data:
                flash('Email not found', 'error')
                return redirect(url_for('inbox'))
            
            # Fast decryption (single method only)
            encrypted_content = email_data.get('content') or email_data.get('encrypted_content')
            key_id = email_data.get('key_id') or email_data.get('encryption_key_id')
            
            if encrypted_content and key_id and quantum_crypto:
                try:
                    user_keys = key_manager.get_user_keys(session['user_id'], include_expired=True)
                    decryption_key = None
                    
                    for key in user_keys:
                        if key.get('key_id') == key_id:
                            decryption_key = key.get('key_data')
                            break
                    
                    if decryption_key:
                        # Single decryption attempt (base64 method only)
                        if isinstance(decryption_key, str):
                            try:
                                decryption_key = base64.b64decode(decryption_key)
                            except:
                                decryption_key = decryption_key.encode('utf-8')
                        
                        encrypted_bytes = base64.b64decode(encrypted_content) if isinstance(encrypted_content, str) else encrypted_content
                        decrypted_content = quantum_crypto.decrypt_message(encrypted_bytes, decryption_key)
                        
                        if isinstance(decrypted_content, bytes):
                            decrypted_content = decrypted_content.decode('utf-8')
                    else:
                        decrypted_content = "Decryption key not found"
                        
                except Exception:
                    decrypted_content = "Decryption failed"
            else:
                decrypted_content = "No encrypted content available"
                    
    except Exception as e:
        flash('Error loading email', 'error')
        return redirect(url_for('inbox'))
    
    # Cache result
    result_data = {
        'email': email_data,
        'decrypted_content': decrypted_content,
        'ipfs_document': None  # Skip IPFS for performance
    }
    set_cache(cache_key, result_data, 180)
    
    return render_template('view_email.html', **result_data)

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
    """Fast system status check with caching"""
    cache_key = "system_status"
    cached_status = get_cached(cache_key, 60)  # 1 minute cache
    
    if cached_status:
        return jsonify(cached_status)
    
    # Fast status check (no heavy testing)
    status = {
        'quantum_encryption': quantum_crypto is not None,
        'blockchain_verification': False,  # Disabled for performance
        'ipfs_storage': False,            # Disabled for performance  
        'key_manager': key_manager is not None,
        'database_connected': key_manager is not None,
        'email_client': email_client is not None
    }
    
    set_cache(cache_key, status, 60)
    return jsonify(status)

@app.route('/api/send_email', methods=['POST'])
def send_email():
    """Fast email sending without heavy operations"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        sender = session['user_id']
        recipient = data.get('recipient')
        subject = data.get('subject')
        content = data.get('content')
        
        if not all([recipient, subject, content]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Fast key generation
        key_result = key_manager.generate_quantum_key(
            user_id=sender,
            recipient=recipient,
            purpose='email_encryption'
        )
        
        # Fast encryption
        encrypted_content = quantum_crypto.encrypt_message(content, key_result['key_data'])
        
        # Fast email send (no heavy processing)
        email_send_result = email_client.send_secure_email({
            'sender': sender,
            'recipient': recipient,
            'subject': f"[QuMail] {subject}",
            'encrypted_content': encrypted_content,
            'attachments': []  # No attachments for performance
        })
        
        if email_send_result.get('success'):
            # Single database operation
            key_manager.record_email_sent(
                user_id=sender,
                recipient=recipient,
                subject=subject,
                ipfs_hash=None,
                encryption_key_id=key_result['key_id'],
                encrypted_content=base64.b64encode(encrypted_content if isinstance(encrypted_content, bytes) else encrypted_content.encode('utf-8')).decode('utf-8')
            )
            
            # Share key async
            def share_key_async():
                try:
                    key_manager.share_key_with_recipient(
                        key_id=key_result['key_id'],
                        sender_id=sender,
                        recipient_id=recipient
                    )
                except:
                    pass
            
            thread_pool.submit(share_key_async)
            
            return jsonify({
                'success': True, 
                'message': 'Email sent successfully',
                'encryption_key_id': key_result['key_id']
            })
        else:
            return jsonify({
                'success': False, 
                'error': email_send_result.get('error', 'Send failed')
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'Send failed'}), 500

@app.route('/api/email/<email_id>')
def get_email(email_id):
    """Fast email retrieval with caching"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        cache_key = f"api_email_{email_id}_{session['user_id']}"
        cached_email = get_cached(cache_key, 120)  # 2 minute cache
        
        if cached_email:
            return jsonify({'success': True, 'email': cached_email})
        
        if not key_manager:
            return jsonify({'success': False, 'error': 'Key manager not available'}), 500
            
        # Direct inbox query (faster)
        all_emails = key_manager.get_user_inbox(session['user_id'])
        email_data = None
        
        for email in all_emails:
            if str(email.get('id', '')) == str(email_id):
                email_data = email
                break
        
        if not email_data:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        # Fast decryption (single method)
        decrypted_content = "Encrypted content"
        encrypted_content = email_data.get('encrypted_content')
        key_id = email_data.get('encryption_key_id')
        
        if encrypted_content and key_id and quantum_crypto:
            try:
                user_keys = key_manager.get_user_keys(session['user_id'], include_expired=True)
                
                for key in user_keys:
                    if key.get('key_id') == key_id:
                        encryption_key_data = key.get('key_data')
                        
                        if isinstance(encryption_key_data, str):
                            try:
                                encryption_key_data = base64.b64decode(encryption_key_data)
                            except:
                                encryption_key_data = encryption_key_data.encode('utf-8')
                        
                        # Single decryption attempt (fastest method)
                        encrypted_bytes = base64.b64decode(encrypted_content) if isinstance(encrypted_content, str) else encrypted_content
                        decrypted_content = quantum_crypto.decrypt_message(encrypted_bytes, encryption_key_data)
                        
                        if isinstance(decrypted_content, bytes):
                            decrypted_content = decrypted_content.decode('utf-8')
                        break
                        
            except Exception:
                decrypted_content = "Decryption failed"
        
        response_data = {
            'id': email_data.get('id', ''),
            'sender': session['user_id'],
            'recipient': email_data.get('recipient', ''),
            'subject': email_data.get('subject', ''),
            'content': decrypted_content,
            'timestamp': email_data.get('sent_at', ''),
            'encrypted': True,
            'key_id': key_id or '',
            'ipfs_hash': ''
        }
        
        set_cache(cache_key, response_data, 120)
        return jsonify({'success': True, 'email': response_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to get email'}), 500

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

# All debug functionality removed for maximum performance

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
    """High-performance application entry point"""
    try:
        # Skip directory creation in production
        # create_directories()
        
        # Fast initialization
        initialize_components()
        
        # Production configuration
        port = int(os.getenv('PORT', 10000))
        host = '0.0.0.0' if os.getenv('PORT') else '127.0.0.1'
        
        # Skip database table creation for faster startup
        # Tables should already exist in production
        
        # High-performance Flask configuration
        app.config.update(
            # Performance optimizations
            SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 1 year cache
            JSONIFY_PRETTYPRINT_REGULAR=False,   # Faster JSON
            TEMPLATES_AUTO_RELOAD=False,         # No template reloading
            EXPLAIN_TEMPLATE_LOADING=False,      # No debug info
            PRESERVE_CONTEXT_ON_EXCEPTION=False, # Faster error handling
            MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max
        )
        
        # Run with maximum performance settings
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False,      # No auto-reload
            use_debugger=False,      # No debugger
            use_evalex=False,        # No eval exception
            passthrough_errors=True  # Pass errors for better handling
        )
        
    except Exception as e:
        print(f"Startup failed: {e}")  # Minimal logging
        sys.exit(1)

if __name__ == "__main__":
    main()