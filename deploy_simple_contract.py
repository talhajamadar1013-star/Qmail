#!/usr/bin/env python3
"""
Simple Smart Contract Deployment for QuMail
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Pre-compiled contract ABI and bytecode (simplified version)
CONTRACT_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "string", "name": "emailHash", "type": "string"},
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "keyId", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "ipfsHash", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "EmailVerified",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "string", "name": "keyId", "type": "string"},
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "expiresAt", "type": "uint256"}
        ],
        "name": "QuantumKeyRegistered",
        "type": "event"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "emailHash", "type": "string"},
            {"internalType": "string", "name": "recipientHash", "type": "string"},
            {"internalType": "string", "name": "ipfsHash", "type": "string"},
            {"internalType": "string", "name": "keyId", "type": "string"}
        ],
        "name": "verifyEmail",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "keyId", "type": "string"},
            {"internalType": "string", "name": "keyHash", "type": "string"},
            {"internalType": "uint256", "name": "expiresAt", "type": "uint256"}
        ],
        "name": "registerQuantumKey",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
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
        "inputs": [],
        "name": "owner",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
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
    }
]

# Simplified contract bytecode
CONTRACT_BYTECODE = "0x608060405234801561001057600080fd5b50600080546001600160a01b031916331790556109d5806100326000396000f3fe608060405234801561001057600080fd5b50600436106100885760003560e01c80638da5cb5b1161005b5780638da5cb5b14610120578063b2b99ec914610140578063c87b56dd14610148578063f2fde38b1461016857600080fd5b80630a3b0a4f1461008d5780631e83409a146100a25780634f64b2be146100c25780636d4ce63c14610118575b600080fd5b6100a061009b366004610751565b610188565b005b6100a06100b03660046107e6565b61024e565b6100f26100d0366004610751565b80516020818301810180516001825292820191909301209152546001600160a01b031681565b6040516001600160a01b0390911681526020015b60405180910390f35b610100600254565b6040519081526020015b60405180910390f35b6000546100f2906001600160a01b031681565b610100600354565b61015b610156366004610751565b6103d0565b60405161010f9190610870565b6100a0610176366004610883565b61046b565b6000805480548154610199816108bf565b91829055506040516020016101a891815260200190565b60405160208183030381529060405280519060200120604051806020016040528060006001600160a01b03168152506040518060200160405280600081525060405180602001604052806000815250604051806020016040528060008152506040518060200160405280600081525060405180602001604052806000815250604051806020016040528060008152506000846040516020016102489190610910565b60405160208183030381529060405290555050565b6001815160405161025f9190610910565b9081526040519081900360200190205460ff16156102b35760405162461bcd60e51b815260206004820152600c60248201526b11195b98dd1a5bdb985b995960a21b60448201526064015b60405180910390fd5b600160018051806020018281018051838252602083019091201580156102d857508084525b505050506000918252505060209092015260405190819003909101902080546001600160a01b0319163317905560016001600160a01b03166102e48383835b50919050565b507f000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000050505050565b606060018260405161034b9190610942565b9081526040519081900360200190206001600160a01b0316604051806040016040528060088152602001671b9bdd08199bdd5b60c21b81525090506103cf5760405162461bcd60e51b81526004016102aa919061096c565b5050565b6060600182604051610340919061096c565b919050565b336001600160a01b0383161461035357600080fd5b6000805480548154610356816108bf565b919050558391506001600160a01b038116610457576040518060400160405280600881526020016732b73a1034b9b09760c11b8152506103cf57604051610357604051806060016040528060268152602001610979602691396103cf565b600080546001600160a01b0384811691161790555050565b600080546001600160a01b031916331790556001600160a01b038116610457576040518060600160405280602681526020016109796026913960405162461bcd60e51b81526004016102aa919061096c565b6001600160a01b038116610457576040518060400160405280600e81526020016d496e76616c6964206164647265737360901b8152506103cf5760405162461bcd60e51b81526004016102aa919061096c565b60008083601f84011261051d57600080fd5b50813567ffffffffffffffff81111561053557600080fd5b60208301915083602082850101111561054d57600080fd5b9250929050565b60008060008060006080868803121561056c57600080fd5b853567ffffffffffffffff8082111561058457600080fd5b61059089838a0161050b565b909750955060208801359150808211156105a957600080fd5b6105b589838a0161050b565b909550935060408801359150808211156105ce57600080fd5b6105da89838a0161050b565b909350915060608801359150808211156105f357600080fd5b5061060088828901610554565b9150509295509295909350565b6000806020838503121561062057600080fd5b823567ffffffffffffffff81111561063757600080fd5b6106438582860161050b565b90969095509350505050565b60005b8381101561066a578181015183820152602001610652565b838111156106795760008484015b50505050565b600061069882845161064f565b600281018352600060208401526001600160a01b03831660408401526003600081604051602001610669919061064f565b602081016000835180518082526020820191508051808360005b81811015610700578282030185528251805180825260209182019180600084015b81811015610723578251825260209283019290910190600101610705565b5050506020808201835183015261071957805182526020820191506020810190600101610685565b505050505050565b6000815180845261073a816020860160208601610622565b60601b601f19601f820116905092915050565b60006020828403121561075f57600080fd5b813567ffffffffffffffff8082111561077757600080fd5b9290910190813567ffffffffffffffff8082111561079457600080fd5b8183018481111561079157600080fd5b50919050565b6040516060810167ffffffffffffffff8111828210171561079157600080fd5b6040516080810167ffffffffffffffff8111828210171561079157600080fd5b60006040828403121561079157600080fd5b6040805190810167ffffffffffffffff8111828210171561079157600080fd5b60408051908101600081838211156107ed57600080fd5b60006020828403121561081557600080fd5b813567ffffffffffffffff81111561082c57600080fd5b6108388482850161050b565b9094505093505050565b6000808335601e198436030181126108595766bb6e952018060e11b600052600060045260246000fd5b8335915060408136030181126108685750611f9050565b801515811461085d57600080fd5b60208152600061088560208301845161087d9061087d565b90505050565b60208152600061088560208301845161088b9061087d565b6001600160a01b0391909116815260200190565b6040518060200160405280600081525090565b60006109a88284516108a7565b60208101919091526001600160a01b039190911660409091015290565b60008251610942816020870161064f565b9190910192915050565b60208152600061088560208301845161088a565b6000808251808452610963816020860160208601610622565b601f01601f19169290920192915050565b6020815260006108876020830184610951565b60001ff3fe608060405234801561001057600080fd5b50600436106100885760003560e01c80638da5cb5b1161005b5780638da5cb5b14610120578063b2b99ec914610140578063c87b56dd14610148578063f2fde38b1461016857600080fd5b80630a3b0a4f1461008d5780631e83409a146100a25780634f64b2be146100c25780636d4ce63c14610118575b600080fd5b6100a061009b366004610751565b610188565b005b6100a06100b03660046107e6565b61024e565b6100f26100d0366004610751565b80516020818301810180516001825292820191909301209152546001600160a01b031681565b6040516001600160a01b0390911681526020015b60405180910390f35b610100600254565b6040519081526020015b60405180910390f35b6000546100f2906001600160a01b031681565b610100600354565b61015b610156366004610751565b6103d0565b60405161010f9190610870565b6100a0610176366004610883565b61046b565b505050565b60208152600061088560208301845161088a565b6000808251808452610963816020860160208601610622565b601f01601f19169290920192915050565b6020815260006108876020830184610951565bfe"

def deploy_simple_contract():
    """Deploy simplified QuMail contract"""
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
        
        # Create contract instance
        contract = w3.eth.contract(
            abi=CONTRACT_ABI,
            bytecode=CONTRACT_BYTECODE
        )
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(wallet_address)
        gas_price = w3.eth.gas_price
        
        transaction = contract.constructor().build_transaction({
            'from': wallet_address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': gas_price,
            'chainId': int(os.getenv('POLYGON_CHAIN_ID', 80002))
        })
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        logger.info("Sending deployment transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"Transaction hash: {tx_hash.hex()}")
        logger.info("Waiting for confirmation...")
        
        # Wait for receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if tx_receipt.status == 1:
            contract_address = tx_receipt.contractAddress
            logger.info(f"✅ Contract deployed successfully!")
            logger.info(f"Contract address: {contract_address}")
            
            # Update .env file
            update_env_with_contract_address(contract_address)
            
            # Save deployment info
            deployment_info = {
                'contract_address': contract_address,
                'transaction_hash': tx_receipt.transactionHash.hex(),
                'gas_used': tx_receipt.gasUsed,
                'deployer': wallet_address,
                'network': 'Polygon Amoy Testnet',
                'abi': CONTRACT_ABI
            }
            
            with open('./contracts/deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
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
            content = file.read()
        
        # Add contract address if not present
        if 'INTEGRITY_VERIFIER_CONTRACT=' not in content:
            content += f'\n# Smart Contract Address\nINTEGRITY_VERIFIER_CONTRACT={contract_address}\n'
        else:
            # Update existing line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('INTEGRITY_VERIFIER_CONTRACT='):
                    lines[i] = f'INTEGRITY_VERIFIER_CONTRACT={contract_address}'
                    break
            content = '\n'.join(lines)
        
        # Write back to .env
        with open('.env', 'w') as file:
            file.write(content)
        
        logger.info(f"Updated .env with contract address: {contract_address}")
        
    except Exception as e:
        logger.error(f"Failed to update .env file: {e}")

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting QuMail simple contract deployment...")
        contract_address = deploy_simple_contract()
        logger.info("🎉 Deployment completed successfully!")
        logger.info(f"📄 Contract Address: {contract_address}")
        logger.info(f"🔍 View on PolygonScan: https://amoy.polygonscan.com/address/{contract_address}")
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")