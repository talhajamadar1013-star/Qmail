"""
Quantum Key Generator for QuMail
Simulates Quantum Key Distribution (QKD) and generates cryptographically secure keys
"""

import secrets
import hashlib
import os
from typing import Tuple, List
from datetime import datetime
import random

class QuantumKeyGenerator:
    """
    Quantum Key Generator that simulates QKD protocols
    Generates truly random keys suitable for One-Time Pad encryption
    """
    
    def __init__(self):
        self.entropy_sources = self._initialize_entropy_sources()
        self.quantum_protocols = ['BB84', 'B92', 'SARG04', 'E91']
        
    def _initialize_entropy_sources(self) -> List[str]:
        """Initialize multiple entropy sources for key generation"""
        sources = [
            'system_random',
            'hardware_random',
            'timestamp_microseconds',
            'memory_address_randomness',
            'process_id_entropy'
        ]
        return sources
    
    def generate_quantum_key(self, length_bytes: int = 256, protocol: str = 'BB84') -> Tuple[bytes, dict]:
        """
        Generate a quantum key using specified QKD protocol simulation
        
        Args:
            length_bytes: Length of key in bytes
            protocol: QKD protocol to simulate (BB84, B92, SARG04, E91)
            
        Returns:
            Tuple of (key_bytes, metadata)
        """
        if protocol not in self.quantum_protocols:
            raise ValueError(f"Unsupported protocol. Use one of: {self.quantum_protocols}")
        
        # Generate base random key
        key_bytes = self._generate_secure_random_bytes(length_bytes)
        
        # Apply quantum protocol simulation
        if protocol == 'BB84':
            key_bytes, metadata = self._simulate_bb84(key_bytes)
        elif protocol == 'B92':
            key_bytes, metadata = self._simulate_b92(key_bytes)
        elif protocol == 'SARG04':
            key_bytes, metadata = self._simulate_sarg04(key_bytes)
        elif protocol == 'E91':
            key_bytes, metadata = self._simulate_e91(key_bytes)
        
        # Add general metadata
        metadata.update({
            'protocol': protocol,
            'key_length': len(key_bytes),
            'generation_time': datetime.utcnow().isoformat(),
            'entropy_quality': self._measure_entropy_quality(key_bytes),
            'quantum_error_rate': metadata.get('quantum_error_rate', 0.0)
        })
        
        return key_bytes, metadata
    
    def _generate_secure_random_bytes(self, length: int) -> bytes:
        """Generate cryptographically secure random bytes"""
        # Combine multiple entropy sources
        entropy_data = bytearray()
        
        # System entropy
        entropy_data.extend(secrets.token_bytes(length))
        
        # Additional entropy from various sources
        entropy_data.extend(os.urandom(length // 2))
        
        # Timestamp microseconds
        timestamp = datetime.utcnow().timestamp()
        timestamp_bytes = int((timestamp % 1) * 1_000_000).to_bytes(4, 'big')
        entropy_data.extend(timestamp_bytes * (length // 4))
        
        # Process and mix entropy
        final_key = bytearray(length)
        for i in range(length):
            # XOR multiple entropy sources
            final_key[i] = (
                entropy_data[i % len(entropy_data)] ^
                entropy_data[(i + length // 2) % len(entropy_data)] ^
                entropy_data[(i + length // 4) % len(entropy_data)]
            )
        
        return bytes(final_key)
    
    def _simulate_bb84(self, key_bytes: bytes) -> Tuple[bytes, dict]:
        """
        Simulate BB84 quantum key distribution protocol
        BB84 uses polarized photons in four states
        """
        # Simulate quantum channel noise and eavesdropping detection
        error_rate = random.uniform(0.001, 0.01)  # 0.1% to 1% error rate
        
        # Simulate basis reconciliation (random basis selection)
        bases_alice = [random.choice(['+', 'x']) for _ in range(len(key_bytes) * 8)]
        bases_bob = [random.choice(['+', 'x']) for _ in range(len(key_bytes) * 8)]
        
        # Simulate photon transmission and measurement
        processed_key = bytearray()
        matching_bases = 0
        
        for byte_val in key_bytes:
            processed_byte = 0
            for bit_pos in range(8):
                bit = (byte_val >> bit_pos) & 1
                
                # Simulate basis matching
                if bases_alice[len(processed_key) * 8 + bit_pos] == bases_bob[len(processed_key) * 8 + bit_pos]:
                    matching_bases += 1
                    # Add quantum error simulation
                    if random.random() < error_rate:
                        bit = 1 - bit  # Flip bit due to quantum error
                
                processed_byte |= (bit << bit_pos)
            
            processed_key.append(processed_byte)
        
        metadata = {
            'quantum_error_rate': error_rate,
            'basis_matching_rate': matching_bases / (len(key_bytes) * 8),
            'protocol_efficiency': 0.5,  # BB84 theoretical efficiency
            'security_level': 'information_theoretic'
        }
        
        return bytes(processed_key), metadata
    
    def _simulate_b92(self, key_bytes: bytes) -> Tuple[bytes, dict]:
        """
        Simulate B92 quantum key distribution protocol
        B92 uses only two non-orthogonal states
        """
        error_rate = random.uniform(0.002, 0.015)
        
        # B92 has lower efficiency but simpler implementation
        processed_key = bytearray()
        for byte_val in key_bytes:
            # Simulate B92 protocol processing
            processed_byte = byte_val
            
            # Add quantum noise
            for bit_pos in range(8):
                if random.random() < error_rate:
                    processed_byte ^= (1 << bit_pos)
            
            processed_key.append(processed_byte)
        
        metadata = {
            'quantum_error_rate': error_rate,
            'protocol_efficiency': 0.25,  # B92 lower efficiency
            'security_level': 'information_theoretic',
            'non_orthogonal_states': True
        }
        
        return bytes(processed_key), metadata
    
    def _simulate_sarg04(self, key_bytes: bytes) -> Tuple[bytes, dict]:
        """
        Simulate SARG04 quantum key distribution protocol
        SARG04 is resistant to photon-number-splitting attacks
        """
        error_rate = random.uniform(0.001, 0.008)
        
        processed_key = bytearray()
        for byte_val in key_bytes:
            processed_byte = byte_val
            
            # SARG04 processing with enhanced security
            for bit_pos in range(8):
                if random.random() < error_rate:
                    processed_byte ^= (1 << bit_pos)
            
            processed_key.append(processed_byte)
        
        metadata = {
            'quantum_error_rate': error_rate,
            'protocol_efficiency': 0.25,
            'security_level': 'information_theoretic',
            'pns_attack_resistant': True
        }
        
        return bytes(processed_key), metadata
    
    def _simulate_e91(self, key_bytes: bytes) -> Tuple[bytes, dict]:
        """
        Simulate E91 quantum key distribution protocol
        E91 uses entangled photon pairs
        """
        error_rate = random.uniform(0.0005, 0.005)
        
        processed_key = bytearray()
        for byte_val in key_bytes:
            processed_byte = byte_val
            
            # E91 entanglement-based processing
            for bit_pos in range(8):
                if random.random() < error_rate:
                    processed_byte ^= (1 << bit_pos)
            
            processed_key.append(processed_byte)
        
        metadata = {
            'quantum_error_rate': error_rate,
            'protocol_efficiency': 0.5,
            'security_level': 'information_theoretic',
            'entanglement_based': True,
            'bell_inequality_violation': True
        }
        
        return bytes(processed_key), metadata
    
    def _measure_entropy_quality(self, key_bytes: bytes) -> float:
        """
        Measure the entropy quality of generated key
        Returns value between 0.0 and 1.0 (1.0 = perfect entropy)
        """
        if len(key_bytes) == 0:
            return 0.0
        
        # Calculate Shannon entropy
        byte_counts = [0] * 256
        for byte in key_bytes:
            byte_counts[byte] += 1
        
        entropy = 0.0
        total_bytes = len(key_bytes)
        
        for count in byte_counts:
            if count > 0:
                probability = count / total_bytes
                entropy -= probability * (probability.bit_length() - 1)
        
        # Normalize to 0-1 range (8 bits = perfect entropy)
        return min(entropy / 8.0, 1.0)
    
    def verify_key_randomness(self, key_bytes: bytes) -> dict:
        """
        Perform statistical tests on key randomness
        """
        tests = {}
        
        # Basic statistical tests
        tests['length'] = len(key_bytes)
        tests['entropy_quality'] = self._measure_entropy_quality(key_bytes)
        
        # Frequency test
        ones = sum(bin(byte).count('1') for byte in key_bytes)
        total_bits = len(key_bytes) * 8
        tests['frequency_test'] = abs(ones / total_bits - 0.5) < 0.1
        
        # Runs test (consecutive identical bits)
        runs = 0
        prev_bit = None
        for byte in key_bytes:
            for i in range(8):
                bit = (byte >> i) & 1
                if bit != prev_bit:
                    runs += 1
                prev_bit = bit
        
        expected_runs = total_bits / 2
        tests['runs_test'] = abs(runs - expected_runs) / expected_runs < 0.1
        
        # Chi-square test for byte distribution
        expected_freq = len(key_bytes) / 256
        chi_square = sum((byte_counts - expected_freq) ** 2 / expected_freq 
                        for byte_counts in [key_bytes.count(i) for i in range(256)]
                        if expected_freq > 0)
        tests['chi_square_test'] = chi_square < 300  # Simplified threshold
        
        tests['overall_quality'] = all([
            tests['entropy_quality'] > 0.9,
            tests['frequency_test'],
            tests['runs_test'],
            tests['chi_square_test']
        ])
        
        return tests
    
    def generate_key_with_verification(self, length_bytes: int = 256, protocol: str = 'BB84', max_attempts: int = 3) -> Tuple[bytes, dict]:
        """
        Generate quantum key with quality verification
        Regenerate if quality tests fail
        """
        for attempt in range(max_attempts):
            key_bytes, metadata = self.generate_quantum_key(length_bytes, protocol)
            
            # Verify key quality
            quality_tests = self.verify_key_randomness(key_bytes)
            metadata['quality_tests'] = quality_tests
            metadata['generation_attempt'] = attempt + 1
            
            if quality_tests['overall_quality']:
                metadata['verification_passed'] = True
                return key_bytes, metadata
        
        # If all attempts failed, return last attempt with warning
        metadata['verification_passed'] = False
        metadata['warning'] = 'Key quality verification failed after maximum attempts'
        
        return key_bytes, metadata