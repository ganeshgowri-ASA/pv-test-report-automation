"""
Digital Signature Utilities for ISO 17025 Compliance
Cryptographic signing and verification
"""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Any, Optional
from models.approval_models import DigitalSignature


class SignatureGenerator:
    """Generate and verify digital signatures"""

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize signature generator

        Args:
            secret_key: Secret key for HMAC signing (use secure key in production)
        """
        self.secret_key = secret_key or "ISO17025-PV-TEST-REPORT-SECRET-KEY"

    def generate_signature(
        self,
        user_id: int,
        action: str,
        timestamp: datetime,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        algorithm: str = "SHA256"
    ) -> DigitalSignature:
        """
        Generate cryptographic digital signature

        Args:
            user_id: User performing action
            action: Action being performed
            timestamp: Action timestamp
            data: Additional data to sign
            ip_address: IP address of signer
            algorithm: Hash algorithm (SHA256, SHA512)

        Returns:
            DigitalSignature object
        """
        # Create signing payload
        payload = {
            "user_id": user_id,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "data": data
        }

        # Convert to canonical JSON string
        payload_str = json.dumps(payload, sort_keys=True)

        # Generate signature hash
        if algorithm == "SHA256":
            signature_hash = self._hmac_sha256(payload_str)
        elif algorithm == "SHA512":
            signature_hash = self._hmac_sha512(payload_str)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        return DigitalSignature(
            signature_hash=signature_hash,
            signing_algorithm=algorithm,
            timestamp=timestamp,
            ip_address=ip_address
        )

    def verify_signature(
        self,
        signature: DigitalSignature,
        user_id: int,
        action: str,
        timestamp: datetime,
        data: Dict[str, Any]
    ) -> bool:
        """
        Verify digital signature

        Args:
            signature: Digital signature to verify
            user_id: User ID from action
            action: Action type
            timestamp: Timestamp from action
            data: Data that was signed

        Returns:
            True if signature is valid
        """
        # Recreate signature
        test_signature = self.generate_signature(
            user_id=user_id,
            action=action,
            timestamp=timestamp,
            data=data,
            algorithm=signature.signing_algorithm
        )

        # Compare hashes (constant-time comparison)
        return hmac.compare_digest(
            signature.signature_hash,
            test_signature.signature_hash
        )

    def _hmac_sha256(self, message: str) -> str:
        """Generate HMAC-SHA256 signature"""
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

    def _hmac_sha512(self, message: str) -> str:
        """Generate HMAC-SHA512 signature"""
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()


def verify_signature(
    signature: DigitalSignature,
    user_id: int,
    action: str,
    timestamp: datetime,
    data: Dict[str, Any],
    secret_key: Optional[str] = None
) -> bool:
    """
    Convenience function to verify signature

    Args:
        signature: Digital signature to verify
        user_id: User ID
        action: Action type
        timestamp: Timestamp
        data: Signed data
        secret_key: Secret key for verification

    Returns:
        True if valid
    """
    generator = SignatureGenerator(secret_key)
    return generator.verify_signature(signature, user_id, action, timestamp, data)
