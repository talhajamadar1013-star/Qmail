# 🎉 QuMail - Quantum Secure Email Client

## ✅ Successfully Deployed & Configured

QuMail is a cloud-based email client application that uses Quantum Key Distribution (QKD) to provide quantum-secure email communication. **Now running with Flask web interface and real cloud services!**

### 🔧 System Components

1. **🌐 Flask Web Application** - Running on `http://127.0.0.1:5000`
2. **🔐 Neon Database** - Cloud key storage (no local files)  
3. **⛓️ Smart Contract** - Deployed on Polygon Amoy testnet
4. **📁 IPFS Storage** - Pinata cloud storage for encrypted emails
5. **🔑 Embedded Key Manager** - Cloud-based quantum key management

### 📋 Configuration Summary

| Component | Status | Details |
|-----------|---------|----------|
| **Database** | ✅ Connected | Neon PostgreSQL cloud database |
| **Blockchain** | ✅ Deployed | Contract: `0x8A94f6BAb7A70C981ade6b7b8968ABAd82952098` |
| **IPFS** | ✅ Configured | Pinata API with JWT authentication |
| **Wallet** | ✅ Active | `0xFc078bD8906df7162A4BB0E0492aE900Ab06d4ec` (199+ POL) |
| **Web App** | ✅ Running | Flask development server on port 5000 |

### 🔗 Important Links

- **🌐 QuMail App**: http://127.0.0.1:5000
- **🔍 Smart Contract**: https://amoy.polygonscan.com/address/0x8A94f6BAb7A70C981ade6b7b8968ABAd82952098
- **💰 Get Test POL**: https://faucet.polygon.technology/
- **📁 IPFS Gateway**: https://gateway.pinata.cloud

## Architecture Components

### 1. QuMail Client (Desktop Application)
- **Technology**: Python with PyQt5 GUI
- **Functions**: Compose, encrypt, send, receive, and decrypt emails
- **Connections**: Key Manager API, Pinata IPFS, Polygon Mumbai, SMTP/IMAP

### 2. Key Manager (Cloud API)
- **Technology**: Flask/FastAPI with Neon Database
- **Functions**: Generate and manage quantum keys for OTP encryption
- **Security**: Keys stored securely with blockchain hash verification

### 3. IPFS Storage (Pinata)
- **Purpose**: Store encrypted attachments
- **Returns**: IPFS hashes for secure retrieval

### 4. Blockchain Verification (Polygon Mumbai)
- **Purpose**: Store SHA256 hashes for integrity verification
- **Smart Contract**: IntegrityVerifier for hash storage and verification

## Security Features

- **Maximum Security**: One-Time Pad encryption (theoretically unbreakable)
- **Key Isolation**: Quantum keys only in secure Neon Database
- **Integrity Verification**: Blockchain-based hash verification
- **Secure Transport**: HTTPS for all API communications
- **No Key Reuse**: Each OTP key used only once

## Installation

### Prerequisites
```bash
# Python 3.8+
pip install -r requirements.txt
```

### Environment Setup
1. Configure Neon Database connection
2. Set up Pinata IPFS API credentials
3. Configure Polygon Mumbai testnet access
4. Set up email server credentials (SMTP/IMAP)

### Running the Application
```bash
# Start Key Manager API
cd key_manager
python app.py

# Launch QuMail Client
cd qumail_client
python main.py
```

## Project Structure

```
QUmail/
├── qumail_client/          # Desktop GUI application
│   ├── gui/               # PyQt5 interface components
│   ├── crypto/            # OTP encryption/decryption
│   ├── api/               # API client handlers
│   └── main.py            # Application entry point
├── key_manager/           # Cloud-based key management API
│   ├── app.py             # Flask/FastAPI application
│   ├── database/          # Neon DB models and connections
│   └── quantum/           # Quantum key generation
├── blockchain/            # Smart contracts and blockchain integration
│   ├── contracts/         # Solidity smart contracts
│   └── web3_client.py     # Web3 integration
├── config/                # Configuration files
└── docs/                  # Documentation
```

## Data Flow

1. User composes email in QuMail GUI
2. QuMail requests quantum key from Key Manager API
3. Email and attachments encrypted using OTP
4. Encrypted attachments uploaded to IPFS (Pinata)
5. Key and attachment hashes stored on Polygon Mumbai blockchain
6. Encrypted email sent via SMTP
7. Recipient decrypts using same quantum key
8. Integrity verified against blockchain hashes

## Technologies Used

- **Frontend**: Python PyQt5
- **Backend**: Flask/FastAPI
- **Database**: Neon Database (PostgreSQL)
- **Encryption**: PyCryptodome (OTP implementation)
- **Storage**: IPFS via Pinata API
- **Blockchain**: Polygon Mumbai via Web3.py
- **Email**: smtplib/imaplib

## Security Considerations

- Quantum keys stored only in secure Neon Database
- All API communications over HTTPS
- OTP keys never reused
- Blockchain verification for data integrity
- Encrypted storage at rest

## License

MIT License - See LICENSE file for details

## Contributing

Please read CONTRIBUTING.md for guidelines on contributing to this project.