import json

from fastapi.testclient import TestClient
from nacl.signing import SigningKey

from helpers.config import Settings, get_settings
from main import app

signing_key = SigningKey.generate()
public_key_hex = signing_key.verify_key.encode().hex()


def fake_settings() -> Settings:
    return Settings(
        APP_NAME="test",
        APP_VERSION="0",
        DISCORD_PUBLIC_KEY=public_key_hex,
        DISCORD_APPLICATION_ID="1",
        DISCORD_BOT_TOKEN="test-token",
        DISCORD_GUILD_ID="1",
        DATABASE_URL="postgresql://test"
    )


app.dependency_overrides[get_settings] = fake_settings
client = TestClient(app)

PING_BODY = json.dumps({"type": 1}).encode()


def sign(body: bytes, key: SigningKey = signing_key, timestamp: str = "1700000000") -> dict:
    signature = key.sign(timestamp.encode() + body).signature.hex()
    return {
        "X-Signature-Ed25519": signature,
        "X-Signature-Timestamp": timestamp,
    }


def post(body: bytes, headers: dict):
    return client.post("/api/v1/interactions", content=body, headers=headers)


def test_valid_ping_is_accepted():
    response = post(PING_BODY, sign(PING_BODY))
    assert response.status_code == 200
    assert response.json() == {"type": 1}


def test_signature_from_wrong_key_is_rejected():
    attacker_key = SigningKey.generate()
    response = post(PING_BODY, sign(PING_BODY, key=attacker_key))
    assert response.status_code == 401


def test_tampered_body_is_rejected():
    headers = sign(PING_BODY)
    tampered_body = json.dumps({"type": 2}).encode()
    response = post(tampered_body, headers)
    assert response.status_code == 401


def test_missing_headers_is_rejected():
    response = post(PING_BODY, {})
    assert response.status_code == 401

# ------------------------------------- 

def test_ping_command_replies_with_pong():
    body = json.dumps({"type": 2, "data": {"name": "ping"}}).encode()
    response = post(body, sign(body))
    assert response.status_code == 200
    assert response.json()["type"] == 4
    assert "Pong" in response.json()["data"]["content"]


def test_unknown_command_is_private():
    body = json.dumps({"type": 2, "data": {"name": "nope"}}).encode()
    response = post(body, sign(body))
    assert response.status_code == 200
    assert response.json()["data"]["flags"] == 64