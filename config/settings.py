"""
Configuration settings for QuMail application
"""

import os
from typing import Dict, Any
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

class Config:
    """Configuration class for QuMail"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Database Configuration (Neon)
        self.NEON_DB_HOST = os.getenv('NEON_DB_HOST', '')
        self.NEON_DB_NAME = os.getenv('NEON_DB_NAME', 'neondb')
        self.NEON_DB_USER = os.getenv('NEON_DB_USER', 'neondb_owner')
        self.NEON_DB_PASSWORD = os.getenv('NEON_DB_PASSWORD', '')
        self.NEON_DB_PORT = int(os.getenv('NEON_DB_PORT', '5432'))
        self.DATABASE_URL = os.getenv('DATABASE_URL', '')
        
        # In-built Key Manager Configuration (No External API)
        self.ENABLE_EMBEDDED_KM = os.getenv('ENABLE_EMBEDDED_KM', 'True').lower() == 'true'
        self.KM_LOCAL_PORT = int(os.getenv('KM_LOCAL_PORT', '5001'))
        self.KM_SECRET_KEY = os.getenv('KM_SECRET_KEY', 'default_secret_key_change_me')
        self.LOCAL_KEY_STORAGE_PATH = os.path.expanduser(os.getenv('LOCAL_KEY_STORAGE_PATH', '~/.qumail/keys'))
        self.KEY_ENCRYPTION_PASSWORD = os.getenv('KEY_ENCRYPTION_PASSWORD', '')
        
        # Pinata IPFS Configuration
        self.PINATA_API_KEY = os.getenv('PINATA_API_KEY', '')
        self.PINATA_SECRET_KEY = os.getenv('PINATA_SECRET_KEY', '')
        self.PINATA_JWT = os.getenv('PINATA_JWT', '')
        self.PINATA_BASE_URL = os.getenv('PINATA_BASE_URL', 'https://api.pinata.cloud')
        self.PINATA_GATEWAY_URL = os.getenv('PINATA_GATEWAY_URL', 'https://gateway.pinata.cloud')
        
        # Polygon Amoy Testnet Configuration
        self.POLYGON_RPC_URL = os.getenv('POLYGON_RPC_URL', '')
        self.POLYGON_RPC_URL_BACKUP = os.getenv('POLYGON_RPC_URL_BACKUP', 'https://rpc-amoy.polygon.technology')
        self.POLYGON_CHAIN_ID = int(os.getenv('POLYGON_CHAIN_ID', '80002'))
        self.POLYGON_CURRENCY_SYMBOL = os.getenv('POLYGON_CURRENCY_SYMBOL', 'POL')
        self.POLYGON_NETWORK_NAME = os.getenv('POLYGON_NETWORK_NAME', 'Polygon Amoy Testnet')
        self.POLYGON_FAUCET_URL = os.getenv('POLYGON_FAUCET_URL', 'https://faucet.polygon.technology/')
        
        # Blockchain Configuration
        self.PRIVATE_KEY = os.getenv('PRIVATE_KEY', '')
        self.WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', '')
        self.INTEGRITY_VERIFIER_CONTRACT = os.getenv('INTEGRITY_VERIFIER_CONTRACT', '')
        self.CONTRACT_OWNER_ADDRESS = os.getenv('CONTRACT_OWNER_ADDRESS', '')
        
        # Gas Configuration
        self.MAX_GAS_PRICE = int(os.getenv('MAX_GAS_PRICE', '50000000000'))  # 50 Gwei
        self.GAS_LIMIT = int(os.getenv('GAS_LIMIT', '150000'))
        self.GAS_MULTIPLIER = float(os.getenv('GAS_MULTIPLIER', '1.2'))
        
        # Email Configuration
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
        self.IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))
        self.IMAP_USE_SSL = os.getenv('IMAP_USE_SSL', 'True').lower() == 'true'
        
        self.SYSTEM_EMAIL = os.getenv('SYSTEM_EMAIL', '')
        self.SYSTEM_EMAIL_PASSWORD = os.getenv('SYSTEM_EMAIL_PASSWORD', '')
        
        # Application Configuration
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        self.DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.PORT = int(os.getenv('PORT', '5000'))
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'change_me_in_production')
        self.SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))
        
        # File Handling
        self.MAX_ATTACHMENT_SIZE = self._parse_size(os.getenv('MAX_ATTACHMENT_SIZE', '50MB'))
        self.ALLOWED_ATTACHMENT_TYPES = os.getenv('ALLOWED_ATTACHMENT_TYPES', 'pdf,doc,docx,txt,jpg,jpeg,png,gif,zip,rar,7z').split(',')
        self.TEMP_DIRECTORY = os.getenv('TEMP_DIRECTORY', './temp/qumail')
        
        # Security Configuration
        self.ENCRYPTION_ALGORITHM = os.getenv('ENCRYPTION_ALGORITHM', 'OTP')
        self.DEFAULT_KEY_LENGTH = int(os.getenv('DEFAULT_KEY_LENGTH', '256'))
        self.MIN_KEY_LENGTH = int(os.getenv('MIN_KEY_LENGTH', '64'))
        self.MAX_KEY_LENGTH = int(os.getenv('MAX_KEY_LENGTH', '4096'))
        self.HASH_ALGORITHM = os.getenv('HASH_ALGORITHM', 'SHA256')
        self.QUANTUM_PROTOCOL = os.getenv('QUANTUM_PROTOCOL', 'BB84')
        
        # Key Management
        self.KEY_EXPIRY_HOURS = int(os.getenv('KEY_EXPIRY_HOURS', '24'))
        self.MAX_KEYS_PER_USER = int(os.getenv('MAX_KEYS_PER_USER', '50'))
        self.KEY_GENERATION_TIMEOUT = int(os.getenv('KEY_GENERATION_TIMEOUT', '30'))
        
        # GUI Configuration
        self.WINDOW_TITLE = os.getenv('WINDOW_TITLE', 'QuMail - Quantum Secure Email')
        self.WINDOW_WIDTH = int(os.getenv('WINDOW_WIDTH', '1200'))
        self.WINDOW_HEIGHT = int(os.getenv('WINDOW_HEIGHT', '800'))
        self.THEME = os.getenv('THEME', 'dark')
        self.FONT_FAMILY = os.getenv('FONT_FAMILY', 'Arial')
        self.FONT_SIZE = int(os.getenv('FONT_SIZE', '10'))
        self.ENABLE_HIGH_DPI = os.getenv('ENABLE_HIGH_DPI', 'True').lower() == 'true'
        
        # Security & Rate Limiting
        self.MAX_EMAILS_PER_HOUR = int(os.getenv('MAX_EMAILS_PER_HOUR', '100'))
        self.MAX_KEYS_PER_HOUR = int(os.getenv('MAX_KEYS_PER_HOUR', '50'))
        self.MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
        self.ENABLE_ENCRYPTION_VERIFICATION = os.getenv('ENABLE_ENCRYPTION_VERIFICATION', 'True').lower() == 'true'
        self.AUTO_LOCK_MINUTES = int(os.getenv('AUTO_LOCK_MINUTES', '15'))
        
        # Logging
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/qumail.log')
        self.LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10485760'))
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '3'))
        self.ENABLE_CONSOLE_LOGGING = os.getenv('ENABLE_CONSOLE_LOGGING', 'True').lower() == 'true'
        
        # Local Storage
        self.LOCAL_DATA_PATH = os.path.expanduser(os.getenv('LOCAL_DATA_PATH', '~/.qumail'))
        self.LOCAL_DB_PATH = os.path.expanduser(os.getenv('LOCAL_DB_PATH', '~/.qumail/local.db'))
        self.BACKUP_KEYS_LOCALLY = os.getenv('BACKUP_KEYS_LOCALLY', 'True').lower() == 'true'
        self.ENCRYPTED_LOCAL_STORAGE = os.getenv('ENCRYPTED_LOCAL_STORAGE', 'True').lower() == 'true'
        
        # Feature Flags
        self.ENABLE_BLOCKCHAIN_VERIFICATION = os.getenv('ENABLE_BLOCKCHAIN_VERIFICATION', 'True').lower() == 'true'
        self.ENABLE_IPFS_STORAGE = os.getenv('ENABLE_IPFS_STORAGE', 'True').lower() == 'true'
        self.ENABLE_EMAIL_ENCRYPTION = os.getenv('ENABLE_EMAIL_ENCRYPTION', 'True').lower() == 'true'
        self.ENABLE_KEY_EXPIRATION = os.getenv('ENABLE_KEY_EXPIRATION', 'True').lower() == 'true'
        self.ENABLE_MULTI_RECIPIENT = os.getenv('ENABLE_MULTI_RECIPIENT', 'True').lower() == 'true'
        self.ENABLE_OFFLINE_MODE = os.getenv('ENABLE_OFFLINE_MODE', 'True').lower() == 'true'
        
        # Ensure directories exist
        self._create_directories()
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '50MB' to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.LOCAL_DATA_PATH,
            self.LOCAL_KEY_STORAGE_PATH,
            self.TEMP_DIRECTORY,
            os.path.dirname(self.LOG_FILE_PATH),
            os.path.dirname(self.LOCAL_DB_PATH)
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_database_url(self) -> str:
        """Get complete database URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if self.NEON_DB_HOST and self.NEON_DB_USER and self.NEON_DB_PASSWORD:
            return f"postgresql://{self.NEON_DB_USER}:{self.NEON_DB_PASSWORD}@{self.NEON_DB_HOST}:{self.NEON_DB_PORT}/{self.NEON_DB_NAME}?sslmode=require"
        
        return ""
    
    def get_polygon_rpc_url(self) -> str:
        """Get Polygon RPC URL with fallback"""
        return self.POLYGON_RPC_URL or self.POLYGON_RPC_URL_BACKUP
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == 'production'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)"""
        return {
            'ENVIRONMENT': self.ENVIRONMENT,
            'DEBUG': self.DEBUG,
            'ENABLE_EMBEDDED_KM': self.ENABLE_EMBEDDED_KM,
            'POLYGON_NETWORK_NAME': self.POLYGON_NETWORK_NAME,
            'POLYGON_CHAIN_ID': self.POLYGON_CHAIN_ID,
            'ENCRYPTION_ALGORITHM': self.ENCRYPTION_ALGORITHM,
            'DEFAULT_KEY_LENGTH': self.DEFAULT_KEY_LENGTH,
            'QUANTUM_PROTOCOL': self.QUANTUM_PROTOCOL,
            'WINDOW_TITLE': self.WINDOW_TITLE,
            'THEME': self.THEME,
            'ENABLE_BLOCKCHAIN_VERIFICATION': self.ENABLE_BLOCKCHAIN_VERIFICATION,
            'ENABLE_IPFS_STORAGE': self.ENABLE_IPFS_STORAGE,
            'ENABLE_EMAIL_ENCRYPTION': self.ENABLE_EMAIL_ENCRYPTION
        }

def load_config() -> Config:
    """Load configuration from environment"""
    return Config()