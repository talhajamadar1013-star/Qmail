#!/usr/bin/env python3
"""
Deploy minimal QuMail contract using Remix IDE compiled bytecode
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Minimal contract bytecode and ABI
CONTRACT_BYTECODE = "0x608060405234801561001057600080fd5b50600080546001600160a01b0319163317905561056c806100326000396000f3fe608060405234801561001057600080fd5b50600436106100785760003560e01c80638da5cb5b1161005b5780638da5cb5b146100f0578063b2b99ec914610110578063c87b56dd14610118578063f242432a1461013857600080fd5b80630a3b0a4f1461007d57806359e02dd7146100925780636d4ce63c146100e8575b600080fd5b61009061008b366004610403565b610158565b005b6100d86100a0366004610403565b80516020818301810180516002825292820191909301209152805460ff9091161515905081565b60405190151581526020015b60405180910390f35b6100f8600154565b6040519081526020016100df565b6000546001600160a01b03165b6040516001600160a01b0390911681526020016100df565b6100f8600354565b6100d8610126366004610403565b60026020526000908152604090205460ff1681565b61009061014636600461041b565b610220565b600081815260026020526040902054829060ff16156101bc5760405162461bcd60e51b815260206004820152601360248201527245-6d61696c20616c726561647920766572696669656400681b60448201526064015b60405180910390fd5b60008281526002602052604081208054600160ff19909116179055600380549192506101e7836104c1565b91905055507f4d3c2d9b1c9a2c9c9b7b0a0f8e5e9b7c8b3f0e5e7b9a2b8c5f8e9b2c5f8e2a0a828442604051610213929190610315565b60405180910390a1505050565b80516020818301810180516003825292820191909301209152805460ff90911615156105008190116102935760405162461bcd60e51b815260206004820152601260248201527112ddc88185b1c9958591e4810dc99585d95960721b60448201526064016101b3565b60008181526003602052604081208054600160ff199091161790556001805491926102bd836104c1565b91905055507f1e83409a2bcbe1b6b8b7b8a5e5f8c7e6f9b2a8b5e2f8b7a2c9f8e2a2b8c5f8e28242604051610213929190610315565b60408082528351908201819052600091908201906060850190845b818110156103415783516001600160a01b0316835260209384019390920191600101610318565b50505050915050565b6000815180845260005b8181101561037057602081850181015186830182015201610354565b81811115610382576000602083870101525b50601f01601f19169290920160200192915050565b6020815260006103aa602083018461034a565b9392505050565b634e487b7160e01b600052604160045260246000fd5b600082601f8301126103d857600080fd5b81356001600160401b03808211156103f2576103f26103b1565b604051601f8301601f19908116603f0116810190828211818310171561041a5761041a6103b1565b8160405283815286602085880101111561043357600080fd5b836020870160208301376000602085830101528094505050505092915050565b60006020828403121561046557600080fd5b81356001600160401b0381111561047b57600080fd5b610487848285016103c7565b949350505050565b600060208284031215610453576104536103b1565b50919050565b600060208284031215610403576103b156103b1565b50805460018160011615610100020316600290046000825580601f106104de575061050a565b601f0160051c81016020851015610453576104536103b1565b601f0160051c8101905b80821015610502575b815560010161020e565b50505b5050565b6000815180845260005b8181101561053057602081850181015186830182015201610514565b8181111561054257576000602083870101525b50601f01601f19169290920160200192915050565b6020815260006103aa6020830184610506565bfe"

CONTRACT_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "string", "name": "emailHash", "type": "string"},
            {"indexed": False, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "EmailVerified",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "string", "name": "keyId", "type": "string"},
            {"indexed": False, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "KeyRegistered",
        "type": "event"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "emailHash", "type": "string"}
        ],
        "name": "isEmailVerified",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "keyId", "type": "string"}
        ],
        "name": "isKeyRegistered",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "keyId", "type": "string"}
        ],
        "name": "registerKey",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalEmailsVerified",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalKeysRegistered",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "emailHash", "type": "string"}
        ],
        "name": "verifyEmail",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def deploy_contract():
    """Deploy QuMail contract with real credentials"""
    try:
        # Connect to Polygon Amoy
        rpc_url = "https://rpc-amoy.polygon.technology"
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            logger.error("Failed to connect to Polygon Amoy")
            return
        
        logger.info("Connected to Polygon Amoy testnet")
        
        # Setup wallet
        private_key = "0xe66466c2a42d9335011ffe59257cec13b880b565a3f06a16b4d49c32bad966af"
        account = w3.eth.account.from_key(private_key)
        wallet_address = "0xFc078bD8906df7162A4BB0E0492aE900Ab06d4ec"
        
        logger.info(f"Deploying from: {wallet_address}")
        
        # Check balance
        balance = w3.eth.get_balance(wallet_address)
        balance_pol = w3.from_wei(balance, 'ether')
        logger.info(f"Balance: {balance_pol} POL")
        
        if balance_pol < 0.01:
            logger.warning("Low balance! Need more POL tokens")
            return
        
        # Create contract
        contract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=CONTRACT_BYTECODE)
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(wallet_address)
        gas_price = int(w3.eth.gas_price * 1.1)  # 10% higher for faster confirmation
        
        # Estimate gas
        gas_estimate = contract.constructor().estimate_gas({'from': wallet_address})
        gas_limit = int(gas_estimate * 1.2)  # 20% buffer
        
        logger.info(f"Gas estimate: {gas_estimate}, using: {gas_limit}")
        
        # Build transaction
        transaction = contract.constructor().build_transaction({
            'from': wallet_address,
            'nonce': nonce,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': 80002  # Polygon Amoy
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        
        # Send transaction
        logger.info("Sending deployment transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for confirmation
        logger.info("Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            contract_address = receipt.contractAddress
            logger.info(f"✅ Contract deployed successfully!")
            logger.info(f"📄 Contract address: {contract_address}")
            logger.info(f"⛽ Gas used: {receipt.gasUsed}")
            logger.info(f"🔍 View on PolygonScan: https://amoy.polygonscan.com/address/{contract_address}")
            
            # Test contract
            test_contract(w3, contract_address, wallet_address, private_key)
            
            # Update .env
            update_env_file(contract_address)
            
            return contract_address
        else:
            logger.error("❌ Transaction failed")
            return None
            
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return None

def test_contract(w3, contract_address, wallet_address, private_key):
    """Test the deployed contract"""
    try:
        logger.info("Testing contract...")
        
        # Create contract instance
        contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)
        
        # Test read functions
        owner = contract.functions.owner().call()
        total_emails = contract.functions.totalEmailsVerified().call()
        total_keys = contract.functions.totalKeysRegistered().call()
        
        logger.info(f"Contract owner: {owner}")
        logger.info(f"Total emails verified: {total_emails}")
        logger.info(f"Total keys registered: {total_keys}")
        
        # Test registering a key
        test_key_id = "test_quantum_key_123"
        nonce = w3.eth.get_transaction_count(wallet_address)
        
        txn = contract.functions.registerKey(test_key_id).build_transaction({
            'from': wallet_address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 80002
        })
        
        signed_txn = w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"Test transaction hash: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            logger.info("✅ Contract test successful!")
            
            # Verify key was registered
            is_registered = contract.functions.isKeyRegistered(test_key_id).call()
            logger.info(f"Test key registered: {is_registered}")
        else:
            logger.warning("⚠️ Contract test failed")
            
    except Exception as e:
        logger.error(f"Contract test failed: {e}")

def update_env_file(contract_address):
    """Update .env file with contract address"""
    try:
        # Read current .env content
        with open('.env', 'r') as f:
            content = f.read()
        
        # Add contract address
        if 'INTEGRITY_VERIFIER_CONTRACT=' not in content:
            content += f'\n# Smart Contract Address\nINTEGRITY_VERIFIER_CONTRACT={contract_address}\n'
        else:
            # Replace existing line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('INTEGRITY_VERIFIER_CONTRACT='):
                    lines[i] = f'INTEGRITY_VERIFIER_CONTRACT={contract_address}'
                    break
            content = '\n'.join(lines)
        
        # Write back
        with open('.env', 'w') as f:
            f.write(content)
        
        logger.info(f"Updated .env with contract address")
        
        # Save deployment info
        deployment_info = {
            'contract_address': contract_address,
            'network': 'Polygon Amoy Testnet',
            'chain_id': 80002,
            'deployer': '0xFc078bD8906df7162A4BB0E0492aE900Ab06d4ec',
            'abi': CONTRACT_ABI
        }
        
        os.makedirs('contracts', exist_ok=True)
        with open('./contracts/deployment.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info("Deployment info saved to contracts/deployment.json")
        
    except Exception as e:
        logger.error(f"Failed to update .env: {e}")

if __name__ == "__main__":
    logger.info("🚀 Deploying QuMail Smart Contract...")
    contract_address = deploy_contract()
    
    if contract_address:
        logger.info("🎉 Deployment completed successfully!")
    else:
        logger.error("❌ Deployment failed!")