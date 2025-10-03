# QuMail Key Manager REST API Documentation

## Overview

The QuMail Key Manager is a REST API service that provides Quantum Key Distribution (QKD) simulation for secure email communication. It generates, stores, and distributes One-Time Pad (OTP) keys for quantum-secure encryption.

## Base URL

```
http://localhost:5000
```

## Authentication

All key-related endpoints require authentication:

- **Authorization Header**: `Authorization: Bearer <api_token>`
- **User ID Header**: `X-User-ID: <user_email>`

## Core API Endpoints

### 1. Generate New Key

**Endpoint**: `POST /keys`

**Purpose**: Generate a new quantum key for OTP encryption

**Request Headers**:
```
Content-Type: application/json
```

**Request Body** (optional):
```json
{
  "key_length": 256,
  "user_id": "user@example.com"
}
```

**Response** (201 Created):
```json
{
  "key_id": "K123",
  "status": "unused"
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/keys \
  -H "Content-Type: application/json" \
  -d '{"key_length": 256, "user_id": "alice@example.com"}'
```

---

### 2. Fetch Key for Client

**Endpoint**: `GET /keys/<key_id>`

**Purpose**: Retrieve quantum key bytes for encryption/decryption

**Request Headers**:
```
Authorization: Bearer <api_token>
X-User-ID: <user_email>
```

**Response** (200 OK):
```json
{
  "key_id": "K123",
  "key_bytes": "deadbeef0123456789abcdef..."
}
```

**Error Responses**:
- `400 Bad Request`: Missing X-User-ID header
- `401 Unauthorized`: Missing or invalid Authorization header
- `404 Not Found`: Key not found or access denied
- `410 Gone`: Key has already been used

**Example**:
```bash
curl -X GET http://localhost:5000/keys/K123 \
  -H "Authorization: Bearer your_api_token" \
  -H "X-User-ID: alice@example.com"
```

---

### 3. Mark Key as Used

**Endpoint**: `PATCH /keys/<key_id>/use`

**Purpose**: Mark a quantum key as used (OTP requirement - keys can only be used once)

**Request Headers**:
```
X-User-ID: <user_email>
```

**Response** (200 OK):
```json
{
  "key_id": "K123",
  "status": "used"
}
```

**Error Responses**:
- `400 Bad Request`: Missing X-User-ID header
- `404 Not Found`: Key not found

**Example**:
```bash
curl -X PATCH http://localhost:5000/keys/K123/use \
  -H "X-User-ID: alice@example.com"
```

---

### 4. Fetch Key Hash for Verification

**Endpoint**: `GET /keys/<key_id>/hash`

**Purpose**: Get SHA256 hash of the key for blockchain verification

**Response** (200 OK):
```json
{
  "key_id": "K123",
  "hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
}
```

**Error Responses**:
- `404 Not Found`: Key not found

**Example**:
```bash
curl -X GET http://localhost:5000/keys/K123/hash
```

---

### 5. Health Check

**Endpoint**: `GET /health`

**Purpose**: Check service health and status

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-09-30T10:30:00.000Z",
  "service": "QuMail Key Manager",
  "version": "1.0.0"
}
```

**Example**:
```bash
curl -X GET http://localhost:5000/health
```

---

## API Workflow

### Typical Usage Flow:

1. **Generate Key**: Client requests a new quantum key
   ```
   POST /keys → {key_id: "K123", status: "unused"}
   ```

2. **Fetch Key**: Client retrieves key bytes for encryption
   ```
   GET /keys/K123 → {key_id: "K123", key_bytes: "deadbeef..."}
   ```

3. **Get Hash**: (Optional) Get key hash for blockchain storage
   ```
   GET /keys/K123/hash → {key_id: "K123", hash: "sha256hash"}
   ```

4. **Mark Used**: After encryption/decryption, mark key as used
   ```
   PATCH /keys/K123/use → {key_id: "K123", status: "used"}
   ```

5. **Subsequent Access**: Attempts to fetch used key will fail
   ```
   GET /keys/K123 → 410 Gone (Key has already been used)
   ```

---

## Security Features

### One-Time Pad (OTP) Enforcement
- Keys can only be retrieved once for encryption
- Used keys are permanently marked and cannot be reused
- This ensures perfect forward secrecy

### Quantum Key Generation
- Keys generated using quantum simulation algorithms
- Multiple entropy sources for maximum randomness
- Statistical validation for key quality

### Blockchain Integration Ready
- Key hashes available for blockchain storage
- Integrity verification through distributed ledger
- Tamper detection capabilities

---

## Error Handling

### Standard HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **404 Not Found**: Resource not found
- **410 Gone**: Resource no longer available (used key)
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "error": "Error description",
  "message": "Detailed error message"
}
```

---

## Configuration

### Environment Variables

```bash
# Database Configuration
NEON_DB_HOST=your-neon-host.neon.tech
NEON_DB_NAME=qumail_db
NEON_DB_USER=your_username
NEON_DB_PASSWORD=your_password
NEON_DB_PORT=5432

# API Configuration
DEBUG=True
LOG_LEVEL=INFO
PORT=5000

# Security Configuration
KEY_LENGTH=256
HASH_ALGORITHM=SHA256
```

---

## Testing

### Run API Tests

```bash
# Start the API server
python key_manager/start.py

# Run test suite (in another terminal)
python key_manager/test_api.py

# Test with custom server
python key_manager/test_api.py http://your-server.com your_api_token
```

### Manual Testing with curl

```bash
# Generate key
curl -X POST http://localhost:5000/keys \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test@example.com"}'

# Fetch key (replace K123 with actual key_id)
curl -X GET http://localhost:5000/keys/K123 \
  -H "Authorization: Bearer test_token" \
  -H "X-User-ID: test@example.com"

# Mark as used
curl -X PATCH http://localhost:5000/keys/K123/use \
  -H "X-User-ID: test@example.com"
```

---

## Database Schema

### quantum_keys Table

| Column | Type | Description |
|--------|------|-------------|
| key_id | VARCHAR(64) | Unique key identifier (Primary Key) |
| key_bytes | BYTEA | Encrypted quantum key data |
| status | VARCHAR(20) | Key status (unused/used/expired) |
| timestamp | TIMESTAMP | Creation timestamp |
| created_for | VARCHAR(255) | User identifier |
| used_by | VARCHAR(255) | User who used the key |
| used_at | TIMESTAMP | When the key was used |
| hash_stored | BOOLEAN | Whether hash is on blockchain |
| blockchain_tx_hash | VARCHAR(66) | Blockchain transaction hash |

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python key_manager/start.py --init-only

# Start API server
python key_manager/start.py
```

### Production Deployment

1. **Environment Setup**: Configure production database and security settings
2. **Database Migration**: Run initialization scripts
3. **API Deployment**: Deploy to cloud platform (Heroku, AWS, GCP, Azure)
4. **Security**: Enable HTTPS, configure API tokens, set up monitoring

---

## Integration Examples

### Python Client Example

```python
import requests

class QuMailKeyClient:
    def __init__(self, api_url, api_token, user_id):
        self.api_url = api_url
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'X-User-ID': user_id,
            'Content-Type': 'application/json'
        }
    
    def generate_key(self, key_length=256):
        response = requests.post(
            f'{self.api_url}/keys',
            json={'key_length': key_length},
            headers=self.headers
        )
        return response.json()
    
    def fetch_key(self, key_id):
        response = requests.get(
            f'{self.api_url}/keys/{key_id}',
            headers=self.headers
        )
        return response.json()
    
    def mark_key_used(self, key_id):
        response = requests.patch(
            f'{self.api_url}/keys/{key_id}/use',
            headers=self.headers
        )
        return response.json()
```

### JavaScript Client Example

```javascript
class QuMailKeyClient {
    constructor(apiUrl, apiToken, userId) {
        this.apiUrl = apiUrl;
        this.headers = {
            'Authorization': `Bearer ${apiToken}`,
            'X-User-ID': userId,
            'Content-Type': 'application/json'
        };
    }
    
    async generateKey(keyLength = 256) {
        const response = await fetch(`${this.apiUrl}/keys`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ key_length: keyLength })
        });
        return await response.json();
    }
    
    async fetchKey(keyId) {
        const response = await fetch(`${this.apiUrl}/keys/${keyId}`, {
            method: 'GET',
            headers: this.headers
        });
        return await response.json();
    }
    
    async markKeyUsed(keyId) {
        const response = await fetch(`${this.apiUrl}/keys/${keyId}/use`, {
            method: 'PATCH',
            headers: this.headers
        });
        return await response.json();
    }
}
```