from app.core.security import (
    create_access_token,
    decode_token,
    decrypt,
    encrypt,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("s3cret-pass")
    assert h != "s3cret-pass"
    assert verify_password("s3cret-pass", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    token = create_access_token("user-123", {"role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"


def test_encryption_roundtrip():
    secret = "sk-super-secret-api-key"
    enc = encrypt(secret)
    assert enc != secret
    assert decrypt(enc) == secret
