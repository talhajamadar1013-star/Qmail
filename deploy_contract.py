#!/usr/bin/env python3
"""
Smart Contract Deployment Script for QuMail
Deploys QuMailIntegrityVerifier contract to Polygon Amoy testnet
"""

import os
import json
from web3 import Web3
from solcx import compile_source, install_solc
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compile_contract():
    """Compile the QuMailIntegrityVerifier contract"""
    try:
        # Install and set Solidity compiler
        try:
            from solcx import install_solc, set_solc_version
            install_solc('0.8.19')
            set_solc_version('0.8.19')
        except Exception as e:
            logger.warning(f"Solc installation warning: {e}")
        
        # Read contract source
        contract_path = './contracts/QuMailIntegrityVerifier.sol'
        with open(contract_path, 'r') as file:
            contract_source = file.read()
        
        # Compile contract
        compiled_sol = compile_source(
            contract_source,
            output_values=['abi', 'bin'],
            solc_version='0.8.19'
        )
        
        # Get contract interface
        contract_id = list(compiled_sol.keys())[0]
        contract_interface = compiled_sol[contract_id]
        
        logger.info("Contract compiled successfully")
        return contract_interface
        
    except Exception as e:
        logger.error(f"Failed to compile contract: {e}")
        raise

def deploy_contract():
    """Deploy contract to Polygon Amoy testnet"""
    try:
        # Connect to Polygon Amoy
        rpc_url = os.getenv('POLYGON_RPC_URL')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise Exception("Failed to connect to Polygon Amoy testnet")
        
        logger.info(f"Connected to Polygon Amoy: {rpc_url}")
        
        # Setup account
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
            
        account = w3.eth.account.from_key(private_key)
        wallet_address = account.address
        
        logger.info(f"Deploying from wallet: {wallet_address}")
        
        # Check balance
        balance = w3.eth.get_balance(wallet_address)
        balance_eth = w3.from_wei(balance, 'ether')
        logger.info(f"Wallet balance: {balance_eth} POL")
        
        if balance_eth < 0.01:
            logger.warning("Low balance! Get POL tokens from: https://faucet.polygon.technology/")
        
        # Compile contract
        contract_interface = compile_contract()
        
        # Create contract instance
        contract = w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        # Get gas price
        gas_price = w3.eth.gas_price
        logger.info(f"Current gas price: {w3.from_wei(gas_price, 'gwei')} Gwei")
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(wallet_address)
        
        # Estimate gas
        try:
            gas_estimate = contract.constructor().estimate_gas({
                'from': wallet_address
            })
            gas_limit = int(gas_estimate * 1.2)  # Add 20% buffer
        except:
            gas_limit = 3000000  # Fallback gas limit
        
        logger.info(f"Estimated gas: {gas_estimate}, Using gas limit: {gas_limit}")
        
        # Build deployment transaction
        transaction = contract.constructor().build_transaction({
            'from': wallet_address,
            'nonce': nonce,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': int(os.getenv('POLYGON_CHAIN_ID', 80002))
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        
        # Send transaction
        logger.info("Sending deployment transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"Transaction hash: {tx_hash.hex()}")
        logger.info("Waiting for transaction confirmation...")
        
        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if tx_receipt.status == 1:
            contract_address = tx_receipt.contractAddress
            logger.info(f"✅ Contract deployed successfully!")
            logger.info(f"Contract address: {contract_address}")
            logger.info(f"Gas used: {tx_receipt.gasUsed}")
            logger.info(f"Transaction hash: {tx_receipt.transactionHash.hex()}")
            
            # Save deployment info
            deployment_info = {
                'contract_address': contract_address,
                'transaction_hash': tx_receipt.transactionHash.hex(),
                'gas_used': tx_receipt.gasUsed,
                'block_number': tx_receipt.blockNumber,
                'deployer': wallet_address,
                'network': 'Polygon Amoy Testnet',
                'chain_id': int(os.getenv('POLYGON_CHAIN_ID', 80002)),
                'abi': contract_interface['abi']
            }
            
            # Save to file
            with open('./contracts/deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info("Deployment info saved to ./contracts/deployment.json")
            
            # Update .env file
            update_env_with_contract_address(contract_address)
            
            return contract_address
            
        else:
            raise Exception("Transaction failed")
            
    except Exception as e:
        logger.error(f"Failed to deploy contract: {e}")
        raise

def update_env_with_contract_address(contract_address):
    """Update .env file with deployed contract address"""
    try:
        # Read current .env
        with open('.env', 'r') as file:
            lines = file.readlines()
        
        # Update or add contract address
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('INTEGRITY_VERIFIER_CONTRACT='):
                lines[i] = f'INTEGRITY_VERIFIER_CONTRACT={contract_address}\n'
                updated = True
                break
        
        if not updated:
            # Add to end of file
            lines.append(f'\n# Smart Contract Address\nINTEGRITY_VERIFIER_CONTRACT={contract_address}\n')
        
        # Write back to .env
        with open('.env', 'w') as file:
            file.writelines(lines)
        
        logger.info(f"Updated .env with contract address: {contract_address}")
        
    except Exception as e:
        logger.error(f"Failed to update .env file: {e}")

def verify_deployment(contract_address):
    """Verify the deployed contract"""
    try:
        rpc_url = os.getenv('POLYGON_RPC_URL')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Load deployment info
        with open('./contracts/deployment.json', 'r') as f:
            deployment_info = json.load(f)
        
        # Create contract instance
        contract = w3.eth.contract(
            address=contract_address,
            abi=deployment_info['abi']
        )
        
        # Test contract functions
        owner = contract.functions.owner().call()
        total_emails = contract.functions.totalEmailsVerified().call()
        total_keys = contract.functions.totalKeysRegistered().call()
        
        logger.info(f"✅ Contract verification successful!")
        logger.info(f"Contract owner: {owner}")
        logger.info(f"Total emails verified: {total_emails}")
        logger.info(f"Total keys registered: {total_keys}")
        
        return True
        
    except Exception as e:
        logger.error(f"Contract verification failed: {e}")
        return False

def main():
    """Main deployment function"""
    try:
        logger.info("🚀 Starting QuMail smart contract deployment...")
        
        # Deploy contract
        contract_address = deploy_contract()
        
        # Verify deployment
        if verify_deployment(contract_address):
            logger.info("🎉 Deployment completed successfully!")
            logger.info(f"📄 Contract Address: {contract_address}")
            logger.info(f"🔍 View on PolygonScan: https://amoy.polygonscan.com/address/{contract_address}")
            logger.info(f"💰 Get test POL: https://faucet.polygon.technology/")
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    main()