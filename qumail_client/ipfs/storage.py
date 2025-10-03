"""
IPFS Storage for QuMail
Stores encrypted emails on IPFS via Pinata
"""

import logging
import json
import requests
import hashlib
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class IPFSStorage:
    """IPFS storage using Pinata service"""
    
    def __init__(self, config):
        self.config = config
        self.api_key = getattr(config, 'PINATA_API_KEY', '')
        self.secret_key = getattr(config, 'PINATA_SECRET_KEY', '')
        self.jwt_token = getattr(config, 'PINATA_JWT', '')
        self.base_url = getattr(config, 'PINATA_BASE_URL', 'https://api.pinata.cloud')
        self.gateway_url = getattr(config, 'PINATA_GATEWAY_URL', 'https://gateway.pinata.cloud')
        logger.info("IPFS storage initialized with Pinata")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Pinata IPFS connection"""
        try:
            # Test authentication with Pinata
            headers = {
                'Authorization': f'Bearer {self.jwt_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.base_url}/data/testAuthentication',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('message') == 'Congratulations! You are communicating with the Pinata API!':
                    logger.info("IPFS Pinata connection successful")
                    return {'success': True, 'message': 'Pinata API connected'}
                else:
                    logger.warning(f"Unexpected Pinata response: {data}")
                    return {'success': False, 'error': 'Unexpected API response'}
            else:
                logger.error(f"Pinata authentication failed: {response.status_code}")
                return {'success': False, 'error': f'Authentication failed: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"IPFS connection test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def store_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store email data on IPFS via Pinata"""
        try:
            if not self.jwt_token:
                logger.warning("IPFS JWT token not configured")
                return {'success': False, 'error': 'IPFS not configured'}
            
            # Test connection first
            connection_test = self.test_connection()
            if not connection_test.get('success'):
                logger.error("IPFS connection test failed")
                return {'success': False, 'error': 'IPFS connection failed'}
            
            # Prepare data for upload
            email_json = json.dumps(email_data, sort_keys=True, indent=2)
            
            # Upload to Pinata
            headers = {
                'Authorization': f'Bearer {self.jwt_token}',
            }
            
            files = {
                'file': ('email.json', email_json, 'application/json')
            }
            
            data = {
                'pinataMetadata': json.dumps({
                    'name': f'QuMail_Email_{int(time.time())}',
                    'keyvalues': {
                        'service': 'QuMail',
                        'type': 'encrypted_email',
                        'timestamp': str(int(time.time()))
                    }
                }),
                'pinataOptions': json.dumps({
                    'cidVersion': 1
                })
            }
            
            response = requests.post(
                f'{self.base_url}/pinning/pinFileToIPFS',
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result.get('IpfsHash')
                
                logger.info(f"Email stored on IPFS: {ipfs_hash}")
                logger.info(f"Email data size: {len(email_json)} bytes")
                
                return {
                    'success': True,
                    'hash': ipfs_hash,
                    'size': len(email_json),
                    'gateway_url': f"{self.gateway_url}/ipfs/{ipfs_hash}",
                    'pinata_response': result
                }
            else:
                logger.error(f"Pinata upload failed: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'Upload failed: {response.status_code}'}
            
        except Exception as e:
            logger.error(f"IPFS storage failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def store_file(self, file_data: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Store individual file on IPFS via Pinata"""
        try:
            if not self.jwt_token:
                logger.warning("IPFS JWT token not configured")
                return {'success': False, 'error': 'IPFS not configured'}
            
            # Prepare file for upload
            headers = {
                'Authorization': f'Bearer {self.jwt_token}',
            }
            
            files = {
                'file': (filename, file_data, content_type or 'application/octet-stream')
            }
            
            data = {
                'pinataMetadata': json.dumps({
                    'name': f'QuMail_Attachment_{filename}_{int(time.time())}',
                    'keyvalues': {
                        'service': 'QuMail',
                        'type': 'attachment',
                        'filename': filename,
                        'timestamp': str(int(time.time()))
                    }
                }),
                'pinataOptions': json.dumps({
                    'cidVersion': 1
                })
            }
            
            response = requests.post(
                f'{self.base_url}/pinning/pinFileToIPFS',
                headers=headers,
                files=files,
                data=data,
                timeout=60  # Longer timeout for file uploads
            )
            
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result.get('IpfsHash')
                
                logger.info(f"File stored on IPFS: {filename} -> {ipfs_hash}")
                logger.info(f"File size: {len(file_data)} bytes")
                
                return {
                    'success': True,
                    'hash': ipfs_hash,
                    'filename': filename,
                    'size': len(file_data),
                    'content_type': content_type,
                    'gateway_url': f"{self.gateway_url}/ipfs/{ipfs_hash}",
                    'pinata_response': result
                }
            else:
                logger.error(f"File upload to Pinata failed: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'Upload failed: {response.status_code}'}
            
        except Exception as e:
            logger.error(f"File storage on IPFS failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def store_email_with_attachments(self, email_data: Dict[str, Any], attachment_files: list = None) -> Dict[str, Any]:
        """Store email with attachments on IPFS"""
        try:
            if not self.jwt_token:
                logger.warning("IPFS JWT token not configured")
                return {'success': False, 'error': 'IPFS not configured'}
            
            # Store attachments first if provided
            attachments_info = []
            if attachment_files:
                for file_info in attachment_files:
                    file_data = file_info.get('data')
                    filename = file_info.get('filename')
                    content_type = file_info.get('content_type')
                    
                    if file_data and filename:
                        attachment_result = self.store_file(file_data, filename, content_type)
                        if attachment_result['success']:
                            attachments_info.append({
                                'filename': filename,
                                'ipfs_hash': attachment_result['hash'],
                                'size': attachment_result['size'],
                                'content_type': content_type,
                                'gateway_url': attachment_result['gateway_url']
                            })
                            logger.info(f"Attachment stored: {filename} -> {attachment_result['hash']}")
                        else:
                            logger.error(f"Failed to store attachment {filename}: {attachment_result['error']}")
            
            # Add attachments info to email data
            email_data_with_attachments = email_data.copy()
            email_data_with_attachments['attachments'] = attachments_info
            email_data_with_attachments['attachment_count'] = len(attachments_info)
            
            # Store the complete email data
            email_result = self.store_email(email_data_with_attachments)
            
            if email_result['success']:
                return {
                    'success': True,
                    'email_hash': email_result['hash'],
                    'attachments': attachments_info,
                    'total_attachments': len(attachments_info),
                    'email_size': email_result['size']
                }
            else:
                return email_result
            
        except Exception as e:
            logger.error(f"Email with attachments storage failed: {e}")
            return {'success': False, 'error': str(e)}

    def store_encrypted_email(self, email_data: Dict[str, Any]) -> Optional[str]:
        """Store encrypted email on IPFS (legacy method)"""
        try:
            result = self.store_email(email_data)
            if result.get('success'):
                return result.get('hash')
            else:
                return None
        except Exception as e:
            logger.error(f"IPFS storage failed: {e}")
            return None
    
    def retrieve_email(self, ipfs_hash: str) -> Dict[str, Any]:
        """Retrieve email data from IPFS with retry logic"""
        try:
            logger.info(f"Retrieving email from IPFS: {ipfs_hash}")
            
            if not ipfs_hash or len(ipfs_hash) < 10:
                logger.error(f"Invalid IPFS hash: {ipfs_hash}")
                return {'success': False, 'error': 'Invalid IPFS hash'}
            
            if not self.jwt_token:
                logger.warning("IPFS JWT token not configured")
                return {'success': False, 'error': 'IPFS not configured'}
            
            # Try multiple gateways and methods
            gateways = [
                f"{self.gateway_url}/ipfs/{ipfs_hash}",
                f"https://ipfs.io/ipfs/{ipfs_hash}",
                f"https://dweb.link/ipfs/{ipfs_hash}"
            ]
            
            for i, gateway_url in enumerate(gateways):
                try:
                    logger.info(f"Trying gateway {i+1}/{len(gateways)}: {gateway_url}")
                    
                    # Add headers for authentication if using Pinata
                    headers = {'Accept': 'application/json'}
                    if 'pinata.cloud' in gateway_url and self.jwt_token:
                        headers['Authorization'] = f'Bearer {self.jwt_token}'
                    
                    response = requests.get(gateway_url, headers=headers, timeout=15)
                    
                    logger.info(f"Gateway {i+1} response: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            # Try to parse as JSON first
                            email_data = response.json()
                            logger.info(f"Successfully retrieved email from IPFS via {gateway_url}")
                            return {
                                'success': True,
                                'data': email_data,
                                'gateway': gateway_url,
                                'size': len(response.text)
                            }
                        except json.JSONDecodeError:
                            # If not JSON, return raw text
                            logger.info(f"Retrieved raw content from IPFS: {len(response.text)} chars")
                            return {
                                'success': True,
                                'data': response.text,
                                'gateway': gateway_url,
                                'size': len(response.text),
                                'content_type': 'text/plain'
                            }
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited by gateway {i+1}, trying next after delay")
                        time.sleep(3)  # Brief pause before trying next gateway
                        continue
                    else:
                        logger.warning(f"Gateway {i+1} returned status {response.status_code}: {response.text[:200]}")
                        continue
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout accessing gateway {i+1}, trying next")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request failed for gateway {i+1}: {e}")
                    continue
            
            # If all gateways failed, return detailed error
            logger.error(f"All {len(gateways)} IPFS gateways failed for hash: {ipfs_hash}")
            return {
                'success': False, 
                'error': f'Failed to retrieve from all {len(gateways)} IPFS gateways',
                'hash': ipfs_hash,
                'gateways_tried': len(gateways)
            }
            
        except Exception as e:
            logger.error(f"IPFS retrieval exception: {e}")
            return {'success': False, 'error': f'Retrieval failed: {str(e)}'}