// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title QuMailIntegrityVerifier
 * @dev Smart contract for verifying email integrity and quantum key authenticity
 * @author QuMail Team
 */
contract QuMailIntegrityVerifier {
    struct EmailRecord {
        address sender;
        string recipientHash; // Hash of recipient for privacy
        string ipfsHash;      // IPFS hash of encrypted email
        string keyId;         // Quantum key ID used for encryption
        uint256 timestamp;
        bool verified;
    }
    
    struct QuantumKey {
        address owner;
        string keyId;
        string keyHash;       // Hash of the quantum key for verification
        uint256 createdAt;
        uint256 expiresAt;
        bool isActive;
        uint256 usageCount;
    }
    
    // Events
    event EmailVerified(
        string indexed emailHash,
        address indexed sender,
        string keyId,
        string ipfsHash,
        uint256 timestamp
    );
    
    event QuantumKeyRegistered(
        string indexed keyId,
        address indexed owner,
        uint256 expiresAt
    );
    
    event QuantumKeyUsed(
        string indexed keyId,
        address indexed user,
        uint256 usageCount
    );
    
    // Storage
    mapping(string => EmailRecord) public emailRecords;
    mapping(string => QuantumKey) public quantumKeys;
    mapping(address => string[]) public userEmails;
    mapping(address => string[]) public userKeys;
    
    // Access control
    address public owner;
    mapping(address => bool) public authorizedNodes;
    
    // Statistics
    uint256 public totalEmailsVerified;
    uint256 public totalKeysRegistered;
    uint256 public totalActiveUsers;
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier onlyAuthorized() {
        require(
            msg.sender == owner || authorizedNodes[msg.sender],
            "Not authorized"
        );
        _;
    }
    
    constructor() {
        owner = msg.sender;
        authorizedNodes[msg.sender] = true;
    }
    
    /**
     * @dev Register a quantum key on the blockchain
     * @param keyId Unique identifier for the quantum key
     * @param keyHash Hash of the quantum key data
     * @param expiresAt Expiration timestamp
     */
    function registerQuantumKey(
        string memory keyId,
        string memory keyHash,
        uint256 expiresAt
    ) external {
        require(bytes(keyId).length > 0, "Key ID cannot be empty");
        require(bytes(keyHash).length > 0, "Key hash cannot be empty");
        require(expiresAt > block.timestamp, "Key already expired");
        require(!quantumKeys[keyId].isActive, "Key already exists");
        
        quantumKeys[keyId] = QuantumKey({
            owner: msg.sender,
            keyId: keyId,
            keyHash: keyHash,
            createdAt: block.timestamp,
            expiresAt: expiresAt,
            isActive: true,
            usageCount: 0
        });
        
        userKeys[msg.sender].push(keyId);
        totalKeysRegistered++;
        
        emit QuantumKeyRegistered(keyId, msg.sender, expiresAt);
    }
    
    /**
     * @dev Verify email integrity and record on blockchain
     * @param emailHash Unique hash of the email
     * @param recipientHash Hash of recipient address
     * @param ipfsHash IPFS hash where encrypted email is stored
     * @param keyId Quantum key ID used for encryption
     */
    function verifyEmail(
        string memory emailHash,
        string memory recipientHash,
        string memory ipfsHash,
        string memory keyId
    ) external {
        require(bytes(emailHash).length > 0, "Email hash cannot be empty");
        require(bytes(ipfsHash).length > 0, "IPFS hash cannot be empty");
        require(bytes(keyId).length > 0, "Key ID cannot be empty");
        require(!emailRecords[emailHash].verified, "Email already verified");
        
        // Verify quantum key exists and is valid
        QuantumKey storage qKey = quantumKeys[keyId];
        require(qKey.isActive, "Quantum key not found or inactive");
        require(qKey.expiresAt > block.timestamp, "Quantum key expired");
        require(
            qKey.owner == msg.sender || authorizedNodes[msg.sender],
            "Not authorized to use this key"
        );
        
        // Record email verification
        emailRecords[emailHash] = EmailRecord({
            sender: msg.sender,
            recipientHash: recipientHash,
            ipfsHash: ipfsHash,
            keyId: keyId,
            timestamp: block.timestamp,
            verified: true
        });
        
        // Update key usage
        qKey.usageCount++;
        
        // Track user emails
        userEmails[msg.sender].push(emailHash);
        totalEmailsVerified++;
        
        emit EmailVerified(emailHash, msg.sender, keyId, ipfsHash, block.timestamp);
        emit QuantumKeyUsed(keyId, msg.sender, qKey.usageCount);
    }
    
    /**
     * @dev Get email verification details
     * @param emailHash Hash of the email to check
     * @return EmailRecord details
     */
    function getEmailRecord(string memory emailHash)
        external
        view
        returns (EmailRecord memory)
    {
        return emailRecords[emailHash];
    }
    
    /**
     * @dev Get quantum key details
     * @param keyId ID of the quantum key
     * @return QuantumKey details
     */
    function getQuantumKey(string memory keyId)
        external
        view
        returns (QuantumKey memory)
    {
        return quantumKeys[keyId];
    }
    
    /**
     * @dev Check if an email is verified
     * @param emailHash Hash of the email
     * @return bool verification status
     */
    function isEmailVerified(string memory emailHash)
        external
        view
        returns (bool)
    {
        return emailRecords[emailHash].verified;
    }
    
    /**
     * @dev Check if a quantum key is valid and active
     * @param keyId ID of the quantum key
     * @return bool validity status
     */
    function isKeyValid(string memory keyId) external view returns (bool) {
        QuantumKey memory qKey = quantumKeys[keyId];
        return qKey.isActive && qKey.expiresAt > block.timestamp;
    }
    
    /**
     * @dev Get user's email history
     * @param user Address of the user
     * @return Array of email hashes
     */
    function getUserEmails(address user)
        external
        view
        returns (string[] memory)
    {
        return userEmails[user];
    }
    
    /**
     * @dev Get user's quantum keys
     * @param user Address of the user
     * @return Array of key IDs
     */
    function getUserKeys(address user)
        external
        view
        returns (string[] memory)
    {
        return userKeys[user];
    }
    
    /**
     * @dev Deactivate an expired or compromised quantum key
     * @param keyId ID of the key to deactivate
     */
    function deactivateKey(string memory keyId) external {
        QuantumKey storage qKey = quantumKeys[keyId];
        require(
            qKey.owner == msg.sender || msg.sender == owner,
            "Not authorized to deactivate this key"
        );
        require(qKey.isActive, "Key already inactive");
        
        qKey.isActive = false;
    }
    
    /**
     * @dev Add authorized node (only owner)
     * @param node Address to authorize
     */
    function addAuthorizedNode(address node) external onlyOwner {
        authorizedNodes[node] = true;
    }
    
    /**
     * @dev Remove authorized node (only owner)
     * @param node Address to remove authorization
     */
    function removeAuthorizedNode(address node) external onlyOwner {
        authorizedNodes[node] = false;
    }
    
    /**
     * @dev Get contract statistics
     * @return totalEmails Total number of verified emails
     * @return totalKeys Total number of registered keys  
     * @return activeUsers Total number of active users
     */
    function getStatistics()
        external
        view
        returns (
            uint256 totalEmails,
            uint256 totalKeys,
            uint256 activeUsers
        )
    {
        return (totalEmailsVerified, totalKeysRegistered, totalActiveUsers);
    }
    
    /**
     * @dev Emergency function to pause contract (only owner)
     */
    bool public paused = false;
    
    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }
    
    function setPaused(bool _paused) external onlyOwner {
        paused = _paused;
    }
}