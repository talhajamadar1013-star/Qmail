"""
QuMail Smart Contract Interaction Module
Simple contract for storing email and key verification hashes
"""

import hashlib
import json
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

class QuMailContract:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("https://rpc-amoy.polygon.technology"))
        self.contract_address = os.getenv('INTEGRITY_VERIFIER_CONTRACT')
        self.private_key = os.getenv('PRIVATE_KEY')
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        
    def verify_email_hash(self, email_content, key_id):
        """Create verification hash for email"""
        combined = f"{email_content}:{key_id}:{self.wallet_address}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def verify_key_hash(self, key_data, user_id):
        """Create verification hash for quantum key"""
        combined = f"{key_data}:{user_id}:{self.wallet_address}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def log_verification(self, hash_value, verification_type):
        """Log verification to blockchain (simulated)"""
        try:
            # In a real implementation, this would send a transaction
            # For now, we'll log locally and return success
            verification_record = {
                'hash': hash_value,
                'type': verification_type,
                'wallet': self.wallet_address,
                'contract': self.contract_address,
                'timestamp': self.w3.eth.get_block('latest')['timestamp'],
                'block_number': self.w3.eth.get_block('latest')['number']
            }
            
            print(f"✅ Verification logged: {verification_record}")
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def get_contract_info(self):
        """Get contract information"""
        if not self.contract_address:
            return None
            
        return {
            'address': self.contract_address,
            'network': 'Polygon Amoy Testnet',
            'explorer': f'https://amoy.polygonscan.com/address/{self.contract_address}',
            'connected': self.w3.is_connected()
        }
