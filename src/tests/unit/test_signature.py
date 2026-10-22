from nacl.signing import SigningKey

from helpers.signature import is_valid_signature

signing_key = SigningKey.generate()
public_key = signing_key.verify_key.encode().hex()

TIMESTAMP = "1700000000"
BODY = b'{"type": 1}'


def make_signature(body: bytes = BODY, timestamp: str = TIMESTAMP, key: SigningKey = signing_key) -> str:
    return key.sign(timestamp.encode() + body).signature.hex()


def test_valid_signature_returns_true():
    assert is_valid_signature(public_key, make_signature(), TIMESTAMP, BODY) is True


def test_signature_from_other_key_returns_false():
    other_signature = make_signature(key=SigningKey.generate())
    assert is_valid_signature(public_key, other_signature, TIMESTAMP, BODY) is False


def test_tampered_body_returns_false():
    signature = make_signature()
    assert is_valid_signature(public_key, signature, TIMESTAMP, b'{"type": 2}') is False


def test_tampered_timestamp_returns_false():
    signature = make_signature()
    assert is_valid_signature(public_key, signature, "1700000001", BODY) is False


def test_non_hex_signature_returns_false_without_crashing():
    assert is_valid_signature(public_key, "not-a-hex-string", TIMESTAMP, BODY) is False


def test_empty_signature_returns_false():
    assert is_valid_signature(public_key, "", TIMESTAMP, BODY) is False