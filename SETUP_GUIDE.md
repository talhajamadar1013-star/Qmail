# QuMail Setup Guide - Embedded System

## 🚀 Quick Start (Updated Configuration)

### 1. Environment Setup

```bash
# Clone or navigate to QuMail directory
cd /Users/razashaikh/Desktop/QUmail

# Install dependencies
pip install -r requirements.txt

# Run setup script
python setup.py
```

### 2. Configuration Changes Made

#### ✅ **Embedded Key Manager**
- **No external API required** - Key Manager runs locally within QuMail client
- Keys stored in encrypted local SQLite database
- Full quantum key generation capabilities built-in

#### ✅ **Polygon Amoy Testnet** (Updated from Mumbai)
- Chain ID: `80002` (new testnet)
- RPC URL: `https://polygon-amoy.g.alchemy.com/v2/YOUR_API_KEY`
- Currency: `POL` (updated token symbol)
- Faucet: `https://faucet.polygon.technology/`

#### ✅ **Neon Database** (Realistic Configuration)
- Simplified connection format
- Default database name: `neondb`
- Default user: `neondb_owner`
- SSL required for secure connections

### 3. Configuration File (.env)

The `.env.example` now includes:

```bash
# ============================================================================
# EMBEDDED KEY MANAGER (No External API)
# ============================================================================
ENABLE_EMBEDDED_KM=True
LOCAL_KEY_STORAGE_PATH=~/.qumail/keys
KEY_ENCRYPTION_PASSWORD=your_master_password_here

# ============================================================================
# NEON DATABASE (Realistic Settings)
# ============================================================================
NEON_DB_HOST=ep-your-endpoint.us-east-1.aws.neon.tech
NEON_DB_NAME=neondb
NEON_DB_USER=neondb_owner
NEON_DB_PASSWORD=your_password_here

# ============================================================================
# POLYGON AMOY TESTNET (Updated)
# ============================================================================
POLYGON_RPC_URL=https://polygon-amoy.g.alchemy.com/v2/YOUR_API_KEY
POLYGON_CHAIN_ID=80002
POLYGON_CURRENCY_SYMBOL=POL
POLYGON_NETWORK_NAME=Polygon Amoy Testnet
```

### 4. Getting Started

1. **Copy configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file with your credentials:**
   - Neon Database credentials from https://console.neon.tech/
   - Pinata IPFS API keys from https://app.pinata.cloud/
   - Alchemy API key for Polygon Amoy from https://dashboard.alchemy.com/

3. **Run setup:**
   ```bash
   python setup.py
   ```

4. **Launch QuMail:**
   ```bash
   python qumail_client/main.py
   ```

### 5. Key Features

#### 🔑 **Embedded Key Manager**
- ✅ Local quantum key generation
- ✅ Encrypted local storage
- ✅ No external API dependencies
- ✅ Same security as cloud version
- ✅ Offline capable

#### 🌐 **Polygon Amoy Support**
- ✅ Latest Polygon testnet
- ✅ Free POL tokens from faucet
- ✅ Active developer community
- ✅ Better performance than Mumbai

#### 🗄️ **Neon Database Integration**
- ✅ Serverless PostgreSQL
- ✅ Automatic scaling
- ✅ Branch-based development
- ✅ Built-in connection pooling

### 6. Architecture Overview

```
QuMail Client (Desktop App)
├── Embedded Key Manager (Local)
│   ├── SQLite Database (Encrypted)
│   ├── Quantum Key Generator
│   └── Local API Interface
├── Blockchain Integration
│   ├── Polygon Amoy Testnet
│   ├── Smart Contract (IntegrityVerifier)
│   └── Hash Verification
├── IPFS Storage
│   ├── Pinata Cloud Service
│   ├── Encrypted Attachments
│   └── Content Addressing
└── Email Integration
    ├── SMTP/IMAP Protocols
    ├── OTP Encryption
    └── Secure Communication
```

### 7. Development Workflow

1. **Local Development:**
   ```bash
   # Setup development environment
   python setup.py
   
   # Test embedded key manager
   python -c "
   from qumail_client.embedded_km.local_key_manager import get_embedded_key_manager
   from config.settings import load_config
   
   config = load_config()
   km = get_embedded_key_manager(config)
   
   # Generate test key
   key = km.generate_quantum_key('test@example.com', 256)
   print(f'Generated key: {key[\"key_id\"]}')
   
   # Get statistics
   stats = km.get_statistics()
   print(f'Total keys: {stats[\"total_keys\"]}')
   "
   ```

2. **Blockchain Testing:**
   ```bash
   # Get testnet POL tokens
   # Visit: https://faucet.polygon.technology/
   
   # Test connection
   python -c "
   from web3 import Web3
   from config.settings import load_config
   
   config = load_config()
   web3 = Web3(Web3.HTTPProvider(config.get_polygon_rpc_url()))
   
   if web3.is_connected():
       print(f'Connected to {config.POLYGON_NETWORK_NAME}')
       print(f'Latest block: {web3.eth.block_number}')
   else:
       print('Connection failed')
   "
   ```

### 8. Security Notes

- 🔐 Keys encrypted at rest using PBKDF2 + Fernet
- 🔑 Master password protects local key storage
- 🌐 All network communications over HTTPS/WSS
- 🔍 Blockchain verification for data integrity
- ⏰ Automatic key expiration and cleanup

### 9. Troubleshooting

#### Database Issues
```bash
# Check Neon database connection
python -c "
from config.settings import load_config
config = load_config()
print(f'Database URL: {config.get_database_url()}')
"
```

#### Key Manager Issues
```bash
# Reset local key storage
rm -rf ~/.qumail/keys.db
python setup.py
```

#### Blockchain Issues
```bash
# Test RPC connection
curl -X POST https://polygon-amoy.g.alchemy.com/v2/YOUR_API_KEY \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### 10. Next Steps

1. ✅ Setup complete with embedded Key Manager
2. ✅ Polygon Amoy testnet configured
3. ✅ Neon database ready
4. 🔄 Create GUI components (next phase)
5. 🔄 Implement email encryption workflow
6. 🔄 Add blockchain smart contracts
7. 🔄 Deploy IPFS attachment system

---

**Ready to start building quantum-secure email communication! 🚀**