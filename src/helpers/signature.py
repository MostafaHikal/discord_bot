from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

# The security gate of the app: the interactions endpoint is public, so this proves a request really came
# from Discord. Without it, anyone could send fake commands, and Discord refuses to accept the endpoint URL.

def is_valid_signature(public_key: str, signature: str, timestamp: str, body: bytes) -> bool:

    """
    Checks Discord's Ed25519 signature over `timestamp + raw body`.
    * `body` must be the exact bytes received; re-serialised JSON would break the check.
    * Returns True only for a valid signature. Wrong or malformed input returns False; never throws.
    """
    
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        # Bad signature, or malformed/empty hex.
        return False