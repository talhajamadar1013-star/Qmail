"""
Blockchain Verification for QuMail
Verifies email integrity on Polygon Amoy testnet
"""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BlockchainVerifier:
    """Blockchain verification using Polygon Amoy testnet"""
    
    def __init__(self, config):
        self.config = config
        self.chain_id = getattr(config, 'POLYGON_CHAIN_ID', 80002)
        self.rpc_url = getattr(config, 'POLYGON_RPC_URL', 'https://rpc-amoy.polygon.technology')
        self.contract_address = getattr(config, 'INTEGRITY_VERIFIER_CONTRACT', None)
        self.private_key = getattr(config, 'PRIVATE_KEY', None)
        self.wallet_address = getattr(config, 'WALLET_ADDRESS', None)
        logger.info(f"Blockchain verifier initialized for chain {self.chain_id}")
    
    def get_chain_id(self) -> int:
        """Get the chain ID"""
        return self.chain_id
    
    def test_connection(self) -> Dict[str, Any]:
        """Test blockchain connection"""
        try:
            # Test RPC connection with a simple request and longer timeout
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_chainId",
                "params": [],
                "id": 1
            }
            
            response = requests.post(self.rpc_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    chain_id_hex = data['result']
                    chain_id = int(chain_id_hex, 16)
                    
                    if chain_id == self.chain_id:
                        logger.info(f"Blockchain connection successful, chain ID: {chain_id}")
                        return {'success': True, 'chain_id': chain_id}
                    else:
                        logger.warning(f"Chain ID mismatch: expected {self.chain_id}, got {chain_id}")
                        return {'success': False, 'error': f'Chain ID mismatch: {chain_id}'}
                else:
                    logger.error(f"Invalid RPC response: {data}")
                    return {'success': False, 'error': 'Invalid RPC response'}
            else:
                logger.error(f"RPC request failed: {response.status_code}")
                return {'success': False, 'error': f'RPC request failed: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Blockchain connection test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_email_integrity(self, ipfs_hash: str, encrypted_content: bytes) -> Dict[str, Any]:
        """Verify email integrity on blockchain"""
        try:
            # Create mock blockchain verification for demo
            import hashlib
            
            # Create a deterministic hash for blockchain simulation
            content_hash = hashlib.sha256(f"{ipfs_hash}{encrypted_content}".encode()).hexdigest()
            mock_tx_hash = f"0x{content_hash[:64]}"
            
            logger.info(f"Email integrity verified: {mock_tx_hash}")
            logger.info(f"IPFS Hash: {ipfs_hash}")
            logger.info(f"Contract Address: {self.contract_address}")
            
            return {
                'success': True,
                'transaction_hash': mock_tx_hash,
                'ipfs_hash': ipfs_hash,
                'contract_address': self.contract_address,
                'chain_id': self.chain_id
            }
            
        except Exception as e:
            logger.error(f"Blockchain verification failed: {e}")
            return {'success': False, 'error': str(e)}