from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


def is_valid_signature(public_key: str, signature: str, timestamp: str, body: bytes) -> bool:
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        return False