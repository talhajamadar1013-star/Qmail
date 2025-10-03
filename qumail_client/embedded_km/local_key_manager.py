"""
Embedded Key Manager for QuMail Client
Local quantum key generation and management without external API dependencies
"""

import os
import sqlite3
import hashlib
import secrets
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class EmbeddedKeyManager:
    """
    Local Key Manager that runs embedded within the QuMail client
    Provides the same functionality as the cloud KM but locally
    """
    
    def __init__(self, config):
        self.config = config
        self.db_path = os.path.join(config.LOCAL_DATA_PATH, 'keys.db')
        self.encryption_key = self._derive_encryption_key()
        self._lock = threading.Lock()
        self._initialize_database()
    
    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from password for local key storage"""
        password = self.config.KEY_ENCRYPTION_PASSWORD.encode() if self.config.KEY_ENCRYPTION_PASSWORD else b'default_password_change_me'
        salt = b'qumail_salt_2025'  # In production, use random salt stored securely
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _initialize_database(self):
        """Initialize local SQLite database for key storage"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS quantum_keys (
                    key_id TEXT PRIMARY KEY,
                    encrypted_key_bytes BLOB NOT NULL,
                    status TEXT DEFAULT 'unused',
                    timestamp TEXT NOT NULL,
                    created_for TEXT NOT NULL,
                    used_by TEXT,
                    used_at TEXT,
                    expiry_time TEXT,
                    quantum_protocol TEXT DEFAULT 'BB84',
                    key_length INTEGER NOT NULL,
                    hash_sha256 TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS key_metadata (
                    key_id TEXT PRIMARY KEY,
                    metadata_json TEXT NOT NULL,
                    blockchain_tx_hash TEXT,
                    ipfs_hash TEXT,
                    verification_status TEXT DEFAULT 'pending'
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_keys_status ON quantum_keys(status)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_keys_user ON quantum_keys(created_for)
            ''')
            
            conn.commit()
    
    def _encrypt_key_bytes(self, key_bytes: bytes) -> bytes:
        """Encrypt key bytes for secure local storage"""
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(key_bytes)
    
    def _decrypt_key_bytes(self, encrypted_bytes: bytes) -> bytes:
        """Decrypt key bytes from local storage"""
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_bytes)
    
    def generate_quantum_key(self, user_id: str, key_length: int = None) -> Dict[str, Any]:
        """
        Generate a new quantum key locally
        
        Args:
            user_id: User identifier
            key_length: Length of key in bytes (default from config)
            
        Returns:
            Dictionary containing key information
        """
        with self._lock:
            try:
                key_length = key_length or self.config.DEFAULT_KEY_LENGTH
                
                # Validate key length
                if key_length < self.config.MIN_KEY_LENGTH or key_length > self.config.MAX_KEY_LENGTH:
                    raise ValueError(f"Key length must be between {self.config.MIN_KEY_LENGTH} and {self.config.MAX_KEY_LENGTH}")
                
                # Generate quantum key using the quantum key generator
                from key_manager.quantum.key_generator import QuantumKeyGenerator
                quantum_gen = QuantumKeyGenerator()
                
                key_bytes, metadata = quantum_gen.generate_key_with_verification(
                    length_bytes=key_length,
                    protocol=self.config.QUANTUM_PROTOCOL
                )
                
                # Generate unique key ID
                key_id = self._generate_key_id(user_id, key_bytes)
                
                # Calculate expiry time
                expiry_time = datetime.utcnow() + timedelta(hours=self.config.KEY_EXPIRY_HOURS)
                
                # Calculate hash
                key_hash = hashlib.sha256(key_bytes).hexdigest()
                
                # Encrypt key bytes for storage
                encrypted_key_bytes = self._encrypt_key_bytes(key_bytes)
                
                # Store in database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT INTO quantum_keys 
                        (key_id, encrypted_key_bytes, status, timestamp, created_for, 
                         expiry_time, quantum_protocol, key_length, hash_sha256)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        key_id,
                        encrypted_key_bytes,
                        'unused',
                        datetime.utcnow().isoformat(),
                        user_id,
                        expiry_time.isoformat(),
                        self.config.QUANTUM_PROTOCOL,
                        key_length,
                        key_hash
                    ))
                    
                    # Store metadata
                    conn.execute('''
                        INSERT INTO key_metadata (key_id, metadata_json)
                        VALUES (?, ?)
                    ''', (key_id, json.dumps(metadata)))
                    
                    conn.commit()
                
                return {
                    'key_id': key_id,
                    'status': 'unused',
                    'key_length': key_length,
                    'hash': key_hash,
                    'timestamp': datetime.utcnow().isoformat(),
                    'expiry_time': expiry_time.isoformat(),
                    'quantum_protocol': self.config.QUANTUM_PROTOCOL,
                    'metadata': metadata
                }
                
            except Exception as e:
                raise Exception(f"Error generating quantum key: {e}")
    
    def get_quantum_key(self, key_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve quantum key by ID
        
        Args:
            key_id: Unique key identifier
            user_id: User requesting the key
            
        Returns:
            Dictionary containing key data or None if not found
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute('''
                        SELECT * FROM quantum_keys 
                        WHERE key_id = ? AND created_for = ?
                    ''', (key_id, user_id))
                    
                    row = cursor.fetchone()
                    if not row:
                        return None
                    
                    # Check if key is expired
                    expiry_time = datetime.fromisoformat(row['expiry_time'])
                    if datetime.utcnow() > expiry_time and row['status'] == 'unused':
                        # Mark as expired
                        conn.execute('''
                            UPDATE quantum_keys 
                            SET status = 'expired' 
                            WHERE key_id = ?
                        ''', (key_id,))
                        conn.commit()
                        return None
                    
                    # Check if already used
                    if row['status'] in ['used', 'expired']:
                        return None
                    
                    # Decrypt key bytes
                    key_bytes = self._decrypt_key_bytes(row['encrypted_key_bytes'])
                    
                    return {
                        'key_id': row['key_id'],
                        'key_bytes': key_bytes,
                        'status': row['status'],
                        'timestamp': row['timestamp'],
                        'key_length': row['key_length'],
                        'hash': row['hash_sha256']
                    }
                    
            except Exception as e:
                raise Exception(f"Error retrieving quantum key: {e}")
    
    def mark_key_used(self, key_id: str, used_by: str) -> bool:
        """
        Mark a quantum key as used
        
        Args:
            key_id: Key identifier
            used_by: User who used the key
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        UPDATE quantum_keys 
                        SET status = 'used', used_by = ?, used_at = ?
                        WHERE key_id = ? AND status = 'unused'
                    ''', (used_by, datetime.utcnow().isoformat(), key_id))
                    
                    conn.commit()
                    return cursor.rowcount > 0
                    
            except Exception as e:
                raise Exception(f"Error marking key as used: {e}")
    
    def get_key_hash(self, key_id: str) -> Optional[str]:
        """
        Get SHA256 hash of the key for verification
        
        Args:
            key_id: Key identifier
            
        Returns:
            Hash string or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT hash_sha256 FROM quantum_keys WHERE key_id = ?
                ''', (key_id,))
                
                row = cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            raise Exception(f"Error getting key hash: {e}")
    
    def get_user_keys(self, user_id: str, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all keys for a user
        
        Args:
            user_id: User identifier
            status: Optional status filter
            limit: Maximum number of keys to return
            
        Returns:
            List of key dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if status:
                    cursor = conn.execute('''
                        SELECT key_id, status, timestamp, key_length, hash_sha256, 
                               quantum_protocol, expiry_time, used_by, used_at
                        FROM quantum_keys 
                        WHERE created_for = ? AND status = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (user_id, status, limit))
                else:
                    cursor = conn.execute('''
                        SELECT key_id, status, timestamp, key_length, hash_sha256,
                               quantum_protocol, expiry_time, used_by, used_at
                        FROM quantum_keys 
                        WHERE created_for = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (user_id, limit))
                
                keys = []
                for row in cursor.fetchall():
                    keys.append({
                        'key_id': row['key_id'],
                        'status': row['status'],
                        'timestamp': row['timestamp'],
                        'key_length': row['key_length'],
                        'hash': row['hash_sha256'],
                        'quantum_protocol': row['quantum_protocol'],
                        'expiry_time': row['expiry_time'],
                        'used_by': row['used_by'],
                        'used_at': row['used_at']
                    })
                
                return keys
                
        except Exception as e:
            raise Exception(f"Error retrieving user keys: {e}")
    
    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired keys
        
        Returns:
            Number of keys marked as expired
        """
        with self._lock:
            try:
                current_time = datetime.utcnow().isoformat()
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        UPDATE quantum_keys 
                        SET status = 'expired'
                        WHERE status = 'unused' AND expiry_time < ?
                    ''', (current_time,))
                    
                    conn.commit()
                    return cursor.rowcount
                    
            except Exception as e:
                raise Exception(f"Error cleaning up expired keys: {e}")
    
    def store_blockchain_hash(self, key_id: str, tx_hash: str) -> bool:
        """
        Store blockchain transaction hash for key verification
        
        Args:
            key_id: Key identifier
            tx_hash: Blockchain transaction hash
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    UPDATE key_metadata 
                    SET blockchain_tx_hash = ?, verification_status = 'verified'
                    WHERE key_id = ?
                ''', (tx_hash, key_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            raise Exception(f"Error storing blockchain hash: {e}")
    
    def _generate_key_id(self, user_id: str, key_bytes: bytes) -> str:
        """Generate unique key ID"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{user_id}:{timestamp}:{len(key_bytes)}:{secrets.token_hex(16)}"
        return 'K' + hashlib.sha256(data.encode()).hexdigest()[:31]  # K + 31 chars = 32 total
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get key manager statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_keys,
                        COUNT(CASE WHEN status = 'unused' THEN 1 END) as unused_keys,
                        COUNT(CASE WHEN status = 'used' THEN 1 END) as used_keys,
                        COUNT(CASE WHEN status = 'expired' THEN 1 END) as expired_keys,
                        COUNT(DISTINCT created_for) as unique_users
                    FROM quantum_keys
                ''')
                
                row = cursor.fetchone()
                
                return {
                    'total_keys': row[0],
                    'unused_keys': row[1],
                    'used_keys': row[2],
                    'expired_keys': row[3],
                    'unique_users': row[4],
                    'database_path': self.db_path
                }
                
        except Exception as e:
            return {'error': str(e)}

# Global embedded key manager instance
_embedded_km: Optional[EmbeddedKeyManager] = None

def get_embedded_key_manager(config=None) -> EmbeddedKeyManager:
    """Get or create embedded key manager instance"""
    global _embedded_km
    
    if _embedded_km is None:
        if config is None:
            from config.settings import load_config
            config = load_config()
        _embedded_km = EmbeddedKeyManager(config)
    
    return _embedded_km