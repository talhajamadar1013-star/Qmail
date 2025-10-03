"""
Database models for QuMail Key Manager using SQLAlchemy
"""

from sqlalchemy import create_engine, Column, String, DateTime, LargeBinary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from typing import Optional

Base = declarative_base()

class QuantumKey(Base):
    """Model for storing quantum keys in Neon Database"""
    
    __tablename__ = 'quantum_keys'
    
    key_id = Column(String(64), primary_key=True, index=True)
    key_bytes = Column(LargeBinary, nullable=False)  # Encrypted OTP key
    status = Column(String(20), default='unused', nullable=False)  # unused/used/expired
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_for = Column(String(255), nullable=True)  # User identifier
    used_by = Column(String(255), nullable=True)  # Who used the key
    used_at = Column(DateTime, nullable=True)  # When the key was used
    hash_stored = Column(Boolean, default=False)  # Whether hash is stored on blockchain
    blockchain_tx_hash = Column(String(66), nullable=True)  # Transaction hash on blockchain
    
    def __repr__(self):
        return f"<QuantumKey(key_id='{self.key_id}', status='{self.status}', created_for='{self.created_for}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'key_id': self.key_id,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_for': self.created_for,
            'used_by': self.used_by,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'hash_stored': self.hash_stored,
            'blockchain_tx_hash': self.blockchain_tx_hash
        }

class EmailMetadata(Base):
    """Model for storing email metadata"""
    
    __tablename__ = 'email_metadata'
    
    email_id = Column(String(64), primary_key=True, index=True)
    sender_email = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    key_id = Column(String(64), nullable=False, index=True)
    ipfs_hash = Column(String(100), nullable=True)  # For attachments
    subject_hash = Column(String(64), nullable=True)  # Encrypted subject hash
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified = Column(Boolean, default=False)  # Blockchain verification status
    
    def __repr__(self):
        return f"<EmailMetadata(email_id='{self.email_id}', sender='{self.sender_email}', recipient='{self.recipient_email}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'email_id': self.email_id,
            'sender_email': self.sender_email,
            'recipient_email': self.recipient_email,
            'key_id': self.key_id,
            'ipfs_hash': self.ipfs_hash,
            'subject_hash': self.subject_hash,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'verified': self.verified
        }

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=os.getenv('DEBUG', 'False').lower() == 'true'
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            print("Database tables created successfully")
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_connection(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get or create database manager instance"""
    global db_manager
    if db_manager is None:
        from config.settings import load_config
        config = load_config()
        db_manager = DatabaseManager(config.get_database_url())
    return db_manager

def get_db_session():
    """Get database session for dependency injection"""
    db = get_database_manager().get_session()
    try:
        yield db
    finally:
        db.close()