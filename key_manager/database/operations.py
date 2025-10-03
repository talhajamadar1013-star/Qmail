"""
Database operations and queries for QuMail Key Manager
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib
import secrets

from .models import QuantumKey, EmailMetadata, get_database_manager

class QuantumKeyService:
    """Service class for quantum key operations"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
    
    def generate_quantum_key(self, user_id: str, key_length: int = 256) -> Dict[str, Any]:
        """
        Generate a new quantum key for OTP encryption
        
        Args:
            user_id: User identifier
            key_length: Length of key in bytes
            
        Returns:
            Dictionary containing key_id and key data
        """
        try:
            # Generate truly random key bytes
            key_bytes = secrets.token_bytes(key_length)
            
            # Generate unique key ID
            key_id = self._generate_key_id(user_id, key_bytes)
            
            # Create quantum key record
            quantum_key = QuantumKey(
                key_id=key_id,
                key_bytes=key_bytes,
                status='unused',
                created_for=user_id,
                timestamp=datetime.utcnow()
            )
            
            # Save to database
            with self.db_manager.get_session() as session:
                session.add(quantum_key)
                session.commit()
                session.refresh(quantum_key)
            
            return {
                'key_id': key_id,
                'key_bytes': key_bytes,
                'status': 'unused',
                'timestamp': quantum_key.timestamp.isoformat()
            }
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error generating quantum key: {e}")
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
        try:
            with self.db_manager.get_session() as session:
                quantum_key = session.query(QuantumKey).filter(
                    QuantumKey.key_id == key_id,
                    QuantumKey.created_for == user_id
                ).first()
                
                if not quantum_key:
                    return None
                
                return {
                    'key_id': quantum_key.key_id,
                    'key_bytes': quantum_key.key_bytes,
                    'status': quantum_key.status,
                    'timestamp': quantum_key.timestamp.isoformat()
                }
                
        except SQLAlchemyError as e:
            raise Exception(f"Database error retrieving quantum key: {e}")
    
    def mark_key_used(self, key_id: str, used_by: str) -> bool:
        """
        Mark a quantum key as used
        
        Args:
            key_id: Key identifier
            used_by: User who used the key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                quantum_key = session.query(QuantumKey).filter(
                    QuantumKey.key_id == key_id
                ).first()
                
                if not quantum_key:
                    return False
                
                quantum_key.status = 'used'
                quantum_key.used_by = used_by
                quantum_key.used_at = datetime.utcnow()
                
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            raise Exception(f"Database error marking key as used: {e}")
    
    def store_blockchain_hash(self, key_id: str, tx_hash: str) -> bool:
        """
        Store blockchain transaction hash for key
        
        Args:
            key_id: Key identifier
            tx_hash: Blockchain transaction hash
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                quantum_key = session.query(QuantumKey).filter(
                    QuantumKey.key_id == key_id
                ).first()
                
                if not quantum_key:
                    return False
                
                quantum_key.hash_stored = True
                quantum_key.blockchain_tx_hash = tx_hash
                
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            raise Exception(f"Database error storing blockchain hash: {e}")
    
    def get_user_keys(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all keys for a user
        
        Args:
            user_id: User identifier
            status: Optional status filter
            
        Returns:
            List of key dictionaries
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(QuantumKey).filter(
                    QuantumKey.created_for == user_id
                )
                
                if status:
                    query = query.filter(QuantumKey.status == status)
                
                keys = query.order_by(QuantumKey.timestamp.desc()).all()
                
                return [key.to_dict() for key in keys]
                
        except SQLAlchemyError as e:
            raise Exception(f"Database error retrieving user keys: {e}")
    
    def _generate_key_id(self, user_id: str, key_bytes: bytes) -> str:
        """Generate unique key ID"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{user_id}:{timestamp}:{len(key_bytes)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

class EmailMetadataService:
    """Service class for email metadata operations"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
    
    def store_email_metadata(self, email_data: Dict[str, Any]) -> str:
        """
        Store email metadata
        
        Args:
            email_data: Dictionary containing email metadata
            
        Returns:
            Email ID
        """
        try:
            email_id = self._generate_email_id(email_data)
            
            metadata = EmailMetadata(
                email_id=email_id,
                sender_email=email_data['sender_email'],
                recipient_email=email_data['recipient_email'],
                key_id=email_data['key_id'],
                ipfs_hash=email_data.get('ipfs_hash'),
                subject_hash=email_data.get('subject_hash'),
                timestamp=datetime.utcnow()
            )
            
            with self.db_manager.get_session() as session:
                session.add(metadata)
                session.commit()
                session.refresh(metadata)
            
            return email_id
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error storing email metadata: {e}")
    
    def get_email_metadata(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve email metadata by ID"""
        try:
            with self.db_manager.get_session() as session:
                metadata = session.query(EmailMetadata).filter(
                    EmailMetadata.email_id == email_id
                ).first()
                
                return metadata.to_dict() if metadata else None
                
        except SQLAlchemyError as e:
            raise Exception(f"Database error retrieving email metadata: {e}")
    
    def mark_email_verified(self, email_id: str) -> bool:
        """Mark email as blockchain verified"""
        try:
            with self.db_manager.get_session() as session:
                metadata = session.query(EmailMetadata).filter(
                    EmailMetadata.email_id == email_id
                ).first()
                
                if not metadata:
                    return False
                
                metadata.verified = True
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            raise Exception(f"Database error marking email as verified: {e}")
    
    def _generate_email_id(self, email_data: Dict[str, Any]) -> str:
        """Generate unique email ID"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{email_data['sender_email']}:{email_data['recipient_email']}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]