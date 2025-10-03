"""
Neon Database Key Manager for QuMail
Stores quantum keys in Neon cloud database instead of local storage
"""

import os
import logging
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class NeonKeyManager:
    """
    Quantum Key Manager using Neon Database for cloud storage            server.sendmail(sender_email, email, text)
            server.quit()
            
            logger.info(f"OTP email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP to {email}: {e}")
            # For development/testing - log the OTP so we can still test the flow
            if self.config.ENVIRONMENT == 'development':
                logger.warning(f"DEVELOPMENT MODE: OTP for {email} is: {otp}")
                logger.warning("Email sending failed but OTP is logged above for testing")
                return True  # Return True in dev mode so registration can continue
            return Falseocal storage - all keys stored securely in cloud
    """
    
    def __init__(self, config):
        """Initialize Neon Key Manager"""
        self.config = config
        self.database_url = config.DATABASE_URL
        self.secret_key = config.KM_SECRET_KEY
        
        # Initialize encryption for key data
        self._init_encryption()
        
        # Initialize database
        self._init_database()
        
        logger.info("Neon Key Manager initialized with cloud storage")
    
    def _init_encryption(self):
        """Initialize encryption for storing key data"""
        # Derive encryption key from secret
        password = self.secret_key.encode()
        salt = b'qumail_neon_salt_2024'  # In production, use random salt per key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher_suite = Fernet(key)
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Create quantum_keys table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS quantum_keys (
                            key_id VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            recipient VARCHAR(255),
                            purpose VARCHAR(255),
                            key_data_encrypted TEXT NOT NULL,
                            key_length INTEGER NOT NULL,
                            quantum_protocol VARCHAR(50) DEFAULT 'BB84',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP,
                            is_active BOOLEAN DEFAULT TRUE,
                            usage_count INTEGER DEFAULT 0,
                            max_usage INTEGER DEFAULT 1,
                            metadata JSONB
                        );
                    """)
                    
                    # Create indexes
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_quantum_keys_user_id 
                        ON quantum_keys(user_id);
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_quantum_keys_expires_at 
                        ON quantum_keys(expires_at);
                    """)
                    
                    # Create email statistics table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS email_statistics (
                            id SERIAL PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            email_type VARCHAR(20) NOT NULL CHECK (email_type IN ('sent', 'received')),
                            recipient VARCHAR(255),
                            sender VARCHAR(255),
                            subject VARCHAR(500),
                            ipfs_hash VARCHAR(100),
                            encryption_key_id VARCHAR(255),
                            encrypted_content TEXT,
                            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # Create user accounts table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_accounts (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            is_verified BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP,
                            failed_login_attempts INTEGER DEFAULT 0,
                            account_locked_until TIMESTAMP,
                            password_reset_token VARCHAR(255),
                            password_reset_expires TIMESTAMP
                        );
                    """)
                    
                    # Create OTP verification table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS otp_verification (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) NOT NULL,
                            otp_code VARCHAR(10) NOT NULL,
                            purpose VARCHAR(50) NOT NULL,
                            expires_at TIMESTAMP NOT NULL,
                            is_used BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            password_hash VARCHAR(255)  -- For storing temp password hash during registration
                        );
                    """)
                    
                    # Add encrypted_content column if it doesn't exist (for existing tables)
                    cur.execute("""
                        ALTER TABLE email_statistics 
                        ADD COLUMN IF NOT EXISTS encrypted_content TEXT;
                    """)
                    
                    # Add password_hash column to otp_verification if it doesn't exist
                    cur.execute("""
                        ALTER TABLE otp_verification 
                        ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
                    """)
                    
                    # Create indexes separately (PostgreSQL syntax)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_email_stats_user_id 
                        ON email_statistics(user_id);
                    """)
                    
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_email_stats_sent_at 
                        ON email_statistics(sent_at);
                    """)
                    
                    conn.commit()
                    logger.info("Database tables initialized successfully")
                    
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def test_connection(self):
        """Test database connection"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def generate_quantum_key(self, user_id: str, recipient: str = None, 
                           purpose: str = "email_encryption", 
                           key_length: int = None) -> Dict[str, Any]:
        """
        Generate a new quantum key and store in Neon database
        
        Args:
            user_id: User identifier
            recipient: Intended recipient (optional)
            purpose: Purpose of the key
            key_length: Length of key in bytes (default from config)
            
        Returns:
            Dictionary with key information
        """
        try:
            if key_length is None:
                key_length = getattr(self.config, 'DEFAULT_KEY_LENGTH', 256)
            
            # Generate quantum key using secure random
            key_data = secrets.token_bytes(key_length)
            key_id = str(uuid.uuid4())
            
            # Calculate expiry
            expiry_hours = getattr(self.config, 'KEY_EXPIRY_HOURS', 24)
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # Encrypt key data for storage
            encrypted_key_data = self.cipher_suite.encrypt(key_data)
            encrypted_key_str = base64.b64encode(encrypted_key_data).decode()
            
            # Store in database
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO quantum_keys 
                        (key_id, user_id, recipient, purpose, key_data_encrypted, 
                         key_length, expires_at, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        key_id,
                        user_id,
                        recipient,
                        purpose,
                        encrypted_key_str,
                        key_length,
                        expires_at,
                        json.dumps({
                            'quantum_protocol': getattr(self.config, 'QUANTUM_PROTOCOL', 'BB84'),
                            'created_by': 'neon_key_manager',
                            'version': '1.0'
                        })
                    ))
                    conn.commit()
            
            logger.info(f"Generated quantum key {key_id} for user {user_id}")
            
            return {
                'key_id': key_id,
                'key_data': key_data,
                'key_length': key_length,
                'user_id': user_id,
                'recipient': recipient,
                'purpose': purpose,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': expires_at.isoformat(),
                'quantum_protocol': getattr(self.config, 'QUANTUM_PROTOCOL', 'BB84')
            }
            
        except Exception as e:
            logger.error(f"Failed to generate quantum key: {e}")
            raise
    
    def get_key(self, key_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a quantum key from Neon database
        
        Args:
            key_id: Key identifier
            user_id: User identifier (for access control)
            
        Returns:
            Key data dictionary or None if not found
        """
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM quantum_keys 
                        WHERE key_id = %s AND user_id = %s AND is_active = TRUE
                    """, (key_id, user_id))
                    
                    row = cur.fetchone()
                    
                    if not row:
                        return None
                    
                    # Check if key has expired
                    if row['expires_at'] and datetime.utcnow() > row['expires_at']:
                        logger.warning(f"Key {key_id} has expired")
                        return None
                    
                    # Decrypt key data
                    encrypted_data = base64.b64decode(row['key_data_encrypted'])
                    key_data = self.cipher_suite.decrypt(encrypted_data)
                    
                    # Update usage count
                    cur.execute("""
                        UPDATE quantum_keys 
                        SET usage_count = usage_count + 1
                        WHERE key_id = %s
                    """, (key_id,))
                    conn.commit()
                    
                    return {
                        'key_id': row['key_id'],
                        'key_data': key_data,
                        'key_length': row['key_length'],
                        'user_id': row['user_id'],
                        'recipient': row['recipient'],
                        'purpose': row['purpose'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'expires_at': row['expires_at'].isoformat() if row['expires_at'] else None,
                        'usage_count': row['usage_count'] + 1,
                        'quantum_protocol': row['quantum_protocol'],
                        'metadata': row['metadata']
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get key {key_id}: {e}")
            raise
    
    def get_user_keys(self, user_id: str, include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        Get all keys for a user from Neon database
        
        Args:
            user_id: User identifier
            include_expired: Whether to include expired keys
            
        Returns:
            List of key dictionaries
        """
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if include_expired:
                        cur.execute("""
                            SELECT key_id, user_id, recipient, purpose, key_length,
                                   created_at, expires_at, usage_count, quantum_protocol,
                                   is_active, metadata, key_data_encrypted
                            FROM quantum_keys 
                            WHERE user_id = %s 
                            ORDER BY created_at DESC
                        """, (user_id,))
                    else:
                        cur.execute("""
                            SELECT key_id, user_id, recipient, purpose, key_length,
                                   created_at, expires_at, usage_count, quantum_protocol,
                                   is_active, metadata, key_data_encrypted
                            FROM quantum_keys 
                            WHERE user_id = %s AND is_active = TRUE 
                            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                            ORDER BY created_at DESC
                        """, (user_id,))
                    
                    rows = cur.fetchall()
                    
                    keys = []
                    for row in rows:
                        # Check if key is expired
                        expired = (row['expires_at'] and 
                                 datetime.utcnow() > row['expires_at'])
                        
                        # Decrypt key data
                        key_data = None
                        if row['key_data_encrypted']:
                            try:
                                encrypted_key_data = base64.b64decode(row['key_data_encrypted'])
                                key_data = self.cipher_suite.decrypt(encrypted_key_data)
                            except Exception as e:
                                logger.error(f"Failed to decrypt key data for {row['key_id']}: {e}")
                        
                        keys.append({
                            'key_id': row['key_id'],
                            'key_data': key_data,
                            'user_id': row['user_id'],
                            'recipient': row['recipient'],
                            'purpose': row['purpose'],
                            'key_length': row['key_length'],
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                            'expires_at': row['expires_at'].isoformat() if row['expires_at'] else None,
                            'usage_count': row['usage_count'],
                            'quantum_protocol': row['quantum_protocol'],
                            'is_active': row['is_active'],
                            'expired': expired,
                            'metadata': row['metadata']
                        })
                    
                    return keys
                    
        except Exception as e:
            logger.error(f"Failed to get user keys for {user_id}: {e}")
            raise
    
    def delete_key(self, key_id: str, user_id: str) -> bool:
        """
        Delete a quantum key from Neon database
        
        Args:
            key_id: Key identifier
            user_id: User identifier (for access control)
            
        Returns:
            True if deleted successfully
        """
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Soft delete - mark as inactive
                    cur.execute("""
                        UPDATE quantum_keys 
                        SET is_active = FALSE 
                        WHERE key_id = %s AND user_id = %s
                    """, (key_id, user_id))
                    
                    if cur.rowcount > 0:
                        conn.commit()
                        logger.info(f"Deleted key {key_id} for user {user_id}")
                        return True
                    else:
                        logger.warning(f"Key {key_id} not found for user {user_id}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to delete key {key_id}: {e}")
            raise
    
    def share_key_with_recipient(self, key_id: str, sender_id: str, recipient_id: str) -> bool:
        """
        Share a quantum key with a recipient by creating a copy for them
        This allows the recipient to decrypt messages encrypted with this key
        
        Args:
            key_id: The key to share
            sender_id: The user who owns the key
            recipient_id: The user to share with
            
        Returns:
            True if successful
        """
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get the original key
                    cur.execute("""
                        SELECT key_data_encrypted, key_length, quantum_protocol, 
                               expires_at, purpose, metadata
                        FROM quantum_keys
                        WHERE key_id = %s AND user_id = %s AND is_active = TRUE
                    """, (key_id, sender_id))
                    
                    key_row = cur.fetchone()
                    if not key_row:
                        logger.error(f"Key {key_id} not found for sender {sender_id}")
                        return False
                    
                    # Create a copy for the recipient with the same key_id
                    # This allows both sender and recipient to decrypt using the same key
                    cur.execute("""
                        INSERT INTO quantum_keys 
                        (key_id, user_id, recipient, purpose, key_data_encrypted, 
                         key_length, quantum_protocol, expires_at, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (key_id, user_id) DO NOTHING
                    """, (
                        key_id,  # Same key_id
                        recipient_id,  # Different user
                        sender_id,  # Track who shared it
                        key_row['purpose'] or 'shared_for_decryption',
                        key_row['key_data_encrypted'],  # Same encrypted key data
                        key_row['key_length'],
                        key_row['quantum_protocol'],
                        key_row['expires_at'],
                        json.dumps(key_row['metadata']) if isinstance(key_row['metadata'], dict) else key_row['metadata']  # Convert dict to JSON string
                    ))
                    
                    conn.commit()
                    logger.info(f"Shared key {key_id} from {sender_id} to {recipient_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to share key {key_id}: {e}")
            return False
    
    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired keys from Neon database
        
        Returns:
            Number of keys cleaned up
        """
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Mark expired keys as inactive
                    cur.execute("""
                        UPDATE quantum_keys 
                        SET is_active = FALSE 
                        WHERE expires_at < CURRENT_TIMESTAMP AND is_active = TRUE
                    """)
                    
                    count = cur.rowcount
                    conn.commit()
                    
                    if count > 0:
                        logger.info(f"Cleaned up {count} expired keys")
                    
                    return count
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            raise
    
    def get_key_statistics(self, user_id: str = None) -> Dict[str, int]:
        """
        Get key usage statistics from Neon database
        
        Args:
            user_id: Optional user filter
            
        Returns:
            Statistics dictionary
        """
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    if user_id:
                        cur.execute("""
                            SELECT 
                                COUNT(*) as total_keys,
                                COUNT(*) FILTER (WHERE is_active = TRUE) as active_keys,
                                COUNT(*) FILTER (WHERE expires_at < CURRENT_TIMESTAMP) as expired_keys,
                                SUM(usage_count) as total_usage
                            FROM quantum_keys 
                            WHERE user_id = %s
                        """, (user_id,))
                    else:
                        cur.execute("""
                            SELECT 
                                COUNT(*) as total_keys,
                                COUNT(*) FILTER (WHERE is_active = TRUE) as active_keys,
                                COUNT(*) FILTER (WHERE expires_at < CURRENT_TIMESTAMP) as expired_keys,
                                SUM(usage_count) as total_usage
                            FROM quantum_keys
                        """)
                    
                    row = cur.fetchone()
                    
                    return {
                        'total_keys': row[0] or 0,
                        'active_keys': row[1] or 0,
                        'expired_keys': row[2] or 0,
                        'total_usage': row[3] or 0
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get key statistics: {e}")
            raise
    
    def record_email_sent(self, user_id: str, recipient: str, subject: str, ipfs_hash: str, encryption_key_id: str, encrypted_content: str = None):
        """Record a sent email for statistics"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO email_statistics 
                        (user_id, email_type, recipient, subject, ipfs_hash, encryption_key_id, encrypted_content)
                        VALUES (%s, 'sent', %s, %s, %s, %s, %s)
                    """, (user_id, recipient, subject, ipfs_hash, encryption_key_id, encrypted_content))
                    conn.commit()
                    logger.info(f"Recorded sent email for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to record sent email: {e}")
    
    def record_email_received(self, user_id: str, sender: str, subject: str, ipfs_hash: str, encryption_key_id: str = None, encrypted_content: str = None):
        """Record a received email for statistics"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO email_statistics 
                        (user_id, email_type, sender, subject, ipfs_hash, encryption_key_id, encrypted_content)
                        VALUES (%s, 'received', %s, %s, %s, %s, %s)
                    """, (user_id, sender, subject, ipfs_hash, encryption_key_id, encrypted_content))
                    conn.commit()
                    logger.info(f"Recorded received email for user {user_id} from {sender}")
        except Exception as e:
            logger.error(f"Failed to record received email: {e}")
    
    def get_user_inbox(self, user_id: str, limit: int = 20) -> list:
        """Get all emails for a user (both sent and received)"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Get both sent and received emails
                    cur.execute("""
                        (SELECT id, 'sent' as type, recipient as other_party, subject, 
                                ipfs_hash, encryption_key_id, encrypted_content, sent_at as timestamp, 
                                recipient as recipient, %s as sender
                         FROM email_statistics 
                         WHERE user_id = %s AND email_type = 'sent')
                        UNION ALL
                        (SELECT id, 'received' as type, sender as other_party, subject, 
                                ipfs_hash, encryption_key_id, encrypted_content, sent_at as timestamp, 
                                %s as recipient, sender
                         FROM email_statistics 
                         WHERE user_id = %s AND email_type = 'received')
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (user_id, user_id, user_id, user_id, limit))
                    
                    emails = []
                    for row in cur.fetchall():
                        email = {
                            'id': row[0],
                            'type': row[1],
                            'other_party': row[2],
                            'subject': row[3],
                            'ipfs_hash': row[4],
                            'encryption_key_id': row[5],
                            'encrypted_content': row[6],
                            'timestamp': row[7],
                            'recipient': row[8],
                            'sender': row[9]
                        }
                        emails.append(email)
                    
                    logger.info(f"Retrieved {len(emails)} emails for user {user_id}")
                    return emails
                    
        except Exception as e:
            logger.error(f"Failed to get user inbox: {e}")
            return []
    
    def get_received_emails(self, user_id: str):
        """Get emails received by user"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, sender, subject, ipfs_hash, encryption_key_id, encrypted_content, 
                               sent_at
                        FROM email_statistics 
                        WHERE user_id = %s AND email_type = 'received'
                        ORDER BY sent_at DESC
                    """, (user_id,))
                    
                    emails = []
                    for row in cur.fetchall():
                        email = {
                            'id': row[0],
                            'sender': row[1],
                            'subject': row[2],
                            'ipfs_hash': row[3],
                            'key_id': row[4],
                            'encryption_key_id': row[4],  # Add this for consistency
                            'content': row[5],
                            'encrypted_content': row[5],  # Add this for consistency
                            'blockchain_hash': None,  # Not stored separately for received emails
                            'timestamp': row[6],
                            'sent_at': row[6]  # Add this for consistency
                        }
                        emails.append(email)
                    
                    logger.info(f"Retrieved {len(emails)} received emails for user {user_id}")
                    return emails
                    
        except Exception as e:
            logger.error(f"Failed to get received emails for user {user_id}: {e}")
            return []
    
    def get_email_statistics(self, user_id: str) -> dict:
        """Get email statistics for a user"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(*) FILTER (WHERE email_type = 'sent') as emails_sent,
                            COUNT(*) FILTER (WHERE email_type = 'received') as emails_received
                        FROM email_statistics 
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    row = cur.fetchone()
                    
                    return {
                        'emails_sent': row[0] or 0,
                        'emails_received': row[1] or 0
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get email statistics: {e}")
            return {'emails_sent': 0, 'emails_received': 0}
    
    def get_sent_emails(self, user_id: str, limit: int = 20) -> list:
        """Get sent emails for a user"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, recipient, subject, ipfs_hash, encryption_key_id, encrypted_content, sent_at
                        FROM email_statistics 
                        WHERE user_id = %s AND email_type = 'sent'
                        ORDER BY sent_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                    
                    emails = []
                    for row in cur.fetchall():
                        email = {
                            'id': row[0],
                            'recipient': row[1],
                            'subject': row[2],
                            'ipfs_hash': row[3],
                            'key_id': row[4],
                            'encryption_key_id': row[4],  # Add this for consistency
                            'content': row[5],
                            'encrypted_content': row[5],  # Add this for consistency
                            'blockchain_hash': None,  # Not stored separately 
                            'timestamp': row[6],
                            'sent_at': row[6]  # Add this for consistency
                        }
                        emails.append(email)
                    
                    return emails
                    
        except Exception as e:
            logger.error(f"Failed to get sent emails: {e}")
            return []

    def delete_email(self, email_id: str, user_id: str) -> bool:
        """Delete an email from the database"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Delete the email, ensuring it belongs to the user
                    cur.execute("""
                        DELETE FROM email_statistics 
                        WHERE id = %s AND user_id = %s
                    """, (email_id, user_id))
                    
                    deleted_count = cur.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"Successfully deleted email {email_id} for user {user_id}")
                        return True
                    else:
                        logger.warning(f"No email found with ID {email_id} for user {user_id}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to delete email {email_id}: {e}")
            return False

    # Authentication Methods
    def _hash_password(self, password: str) -> str:
        """Hash password with salt for secure storage"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, password_hash = stored_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except:
            return False
    
    def _generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return f"{secrets.randbelow(1000000):06d}"
    
    def _send_otp_email(self, email: str, otp: str, purpose: str = "verification") -> bool:
        """Send OTP via email"""
        try:
            # Use configuration settings
            smtp_server = self.config.SMTP_SERVER
            smtp_port = self.config.SMTP_PORT
            sender_email = self.config.SYSTEM_EMAIL
            sender_password = self.config.SYSTEM_EMAIL_PASSWORD
            
            logger.info(f"Attempting to send OTP email from {sender_email} to {email}")
            logger.info(f"SMTP Server: {smtp_server}:{smtp_port}")
            
            # Check if email credentials are configured
            if not sender_email or not sender_password:
                logger.error("SYSTEM_EMAIL and SYSTEM_EMAIL_PASSWORD must be configured in environment variables")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = f"QuMail - {purpose.title()} Code"
            
            body = f"""
            Your QuMail {purpose} code is: {otp}
            
            This code will expire in 10 minutes.
            If you didn't request this, please ignore this email.
            
            - QuMail Security Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            if self.config.SMTP_USE_TLS:
                server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, email, text)
            server.quit()
            
            logger.info(f"OTP sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP to {email}: {e}")
            return False
    
    def create_user_account(self, email: str, password: str) -> dict:
        """Create new user account with OTP verification"""
        try:
            # Check if user already exists
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM user_accounts WHERE email = %s", (email,))
                    if cur.fetchone():
                        return {"success": False, "error": "User already exists"}
            
            # Generate OTP and send email
            otp = self._generate_otp()
            otp_expires = datetime.now() + timedelta(minutes=10)
            
            if not self._send_otp_email(email, otp, "account creation"):
                return {"success": False, "error": "Failed to send verification email"}
            
            # Store pending account with OTP
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Clear any existing OTP for this email
                    cur.execute("DELETE FROM otp_verification WHERE email = %s", (email,))
                    
                    # Store new OTP
                    cur.execute("""
                        INSERT INTO otp_verification (email, otp_code, purpose, expires_at, password_hash)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (email, otp, 'registration', otp_expires, self._hash_password(password)))
                    
                    conn.commit()
                    
            return {"success": True, "message": "Verification code sent to your email"}
            
        except Exception as e:
            logger.error(f"Failed to create account for {email}: {e}")
            return {"success": False, "error": "Failed to create account"}
    
    def verify_registration_otp(self, email: str, otp: str) -> dict:
        """Verify OTP and complete account creation"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Check OTP
                    cur.execute("""
                        SELECT password_hash FROM otp_verification 
                        WHERE email = %s AND otp_code = %s AND purpose = 'registration' 
                        AND expires_at > %s
                    """, (email, otp, datetime.now()))
                    
                    result = cur.fetchone()
                    if not result:
                        return {"success": False, "error": "Invalid or expired verification code"}
                    
                    password_hash = result[0]
                    # Create user account
                    cur.execute("""
                        INSERT INTO user_accounts (email, password_hash, is_verified)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (email, password_hash, True))
                    user_id = cur.fetchone()[0]
                    
                    # Clean up OTP
                    cur.execute("DELETE FROM otp_verification WHERE email = %s", (email,))
                    
                    conn.commit()
                    
            logger.info(f"Account created successfully for {email}")
            return {"success": True, "message": "Account created successfully", "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Failed to verify registration for {email}: {e}")
            return {"success": False, "error": "Failed to create account"}
    
    def authenticate_user(self, email: str, password: str) -> dict:
        """Authenticate user login"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, password_hash, failed_login_attempts, account_locked_until 
                        FROM user_accounts 
                        WHERE email = %s AND is_verified = true
                    """, (email,))
                    
                    result = cur.fetchone()
                    if not result:
                        return {"success": False, "error": "Invalid email or password"}
                    
                    user_id, password_hash, failed_login_attempts, account_locked_until = result
                    
                    # Check if account is locked
                    if account_locked_until and account_locked_until > datetime.now():
                        return {"success": False, "error": "Account temporarily locked. Try again later."}
                    
                    # Verify password
                    if self._verify_password(password, password_hash):
                        # Reset failed attempts on successful login
                        cur.execute("""
                            UPDATE user_accounts 
                            SET failed_login_attempts = 0, account_locked_until = NULL, last_login = %s
                            WHERE id = %s
                        """, (datetime.now(), user_id))
                        conn.commit()
                        
                        logger.info(f"Successful login for user {email}")
                        return {"success": True, "user_id": user_id, "email": email}
                    else:
                        # Increment failed attempts
                        failed_login_attempts = (failed_login_attempts or 0) + 1
                        account_locked_until = None
                        
                        if failed_login_attempts >= 5:
                            account_locked_until = datetime.now() + timedelta(minutes=30)
                        
                        cur.execute("""
                            UPDATE user_accounts 
                            SET failed_login_attempts = %s, account_locked_until = %s
                            WHERE id = %s
                        """, (failed_login_attempts, account_locked_until, user_id))
                        conn.commit()
                        
                        return {"success": False, "error": "Invalid email or password"}
                        
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            return {"success": False, "error": "Authentication failed"}
    
    def initiate_password_reset(self, email: str) -> dict:
        """Initiate password reset with OTP"""
        try:
            # Check if user exists
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM user_accounts WHERE email = %s", (email,))
                    if not cur.fetchone():
                        return {"success": False, "error": "Email not found"}
            
            # Generate OTP and send email
            otp = self._generate_otp()
            otp_expires = datetime.now() + timedelta(minutes=10)
            
            if not self._send_otp_email(email, otp, "password reset"):
                return {"success": False, "error": "Failed to send reset email"}
            
            # Store OTP for password reset
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Clear any existing OTP for this email
                    cur.execute("DELETE FROM otp_verification WHERE email = %s", (email,))
                    
                    # Store new OTP
                    cur.execute("""
                        INSERT INTO otp_verification (email, otp_code, purpose, expires_at)
                        VALUES (%s, %s, %s, %s)
                    """, (email, otp, 'password_reset', otp_expires))
                    
                    conn.commit()
                    
            return {"success": True, "message": "Password reset code sent to your email"}
            
        except Exception as e:
            logger.error(f"Failed to initiate password reset for {email}: {e}")
            return {"success": False, "error": "Failed to send reset email"}
    
    def reset_password_with_otp(self, email: str, otp: str, new_password: str) -> dict:
        """Reset password using OTP"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Verify OTP
                    cur.execute("""
                        SELECT id FROM otp_verification 
                        WHERE email = %s AND otp_code = %s AND purpose = 'password_reset' 
                        AND expires_at > %s
                    """, (email, otp, datetime.now()))
                    
                    if not cur.fetchone():
                        return {"success": False, "error": "Invalid or expired reset code"}
                    
                    # Update password
                    new_password_hash = self._hash_password(new_password)
                    cur.execute("""
                        UPDATE user_accounts 
                        SET password_hash = %s, failed_login_attempts = 0, account_locked_until = NULL
                        WHERE email = %s
                    """, (new_password_hash, email))
                    
                    # Clean up OTP
                    cur.execute("DELETE FROM otp_verification WHERE email = %s", (email,))
                    
                    conn.commit()
                    
            logger.info(f"Password reset successfully for {email}")
            return {"success": True, "message": "Password reset successfully"}
            
        except Exception as e:
            logger.error(f"Failed to reset password for {email}: {e}")
            return {"success": False, "error": "Failed to reset password"}