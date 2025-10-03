// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract QuMailSimple {
    address public owner;
    uint256 public totalEmailsVerified;
    uint256 public totalKeysRegistered;
    
    mapping(string => bool) public verifiedEmails;
    mapping(string => bool) public registeredKeys;
    
    event EmailVerified(string emailHash, address sender, uint256 timestamp);
    event KeyRegistered(string keyId, address owner, uint256 timestamp);
    
    constructor() {
        owner = msg.sender;
    }
    
    function verifyEmail(string memory emailHash) external {
        require(!verifiedEmails[emailHash], "Email already verified");
        verifiedEmails[emailHash] = true;
        totalEmailsVerified++;
        emit EmailVerified(emailHash, msg.sender, block.timestamp);
    }
    
    function registerKey(string memory keyId) external {
        require(!registeredKeys[keyId], "Key already registered");
        registeredKeys[keyId] = true;
        totalKeysRegistered++;
        emit KeyRegistered(keyId, msg.sender, block.timestamp);
    }
    
    function isEmailVerified(string memory emailHash) external view returns (bool) {
        return verifiedEmails[emailHash];
    }
    
    function isKeyRegistered(string memory keyId) external view returns (bool) {
        return registeredKeys[keyId];
    }
}