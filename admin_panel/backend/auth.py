from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json


class AuthError(ValueError):
    pass


def _b64encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return urlsafe_b64decode((data + padding).encode("ascii"))


def create_token(secret: str, ttl_seconds: int) -> str:
    now = datetime.now(timezone.utc)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "admin",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    head = _b64encode(json.dumps(header, separators=(",", ":")).encode())
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{head}.{body}".encode("ascii")
    signature = hmac.new(
        secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{head}.{body}.{_b64encode(signature)}"


def verify_token(token: str, secret: str) -> dict:
    try:
        head, body, signature = token.split(".")
    except ValueError as exc:
        raise AuthError("Invalid token format") from exc

    signing_input = f"{head}.{body}".encode("ascii")
    expected = hmac.new(
        secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    supplied = _b64decode(signature)
    if not hmac.compare_digest(expected, supplied):
        raise AuthError("Invalid token signature")

    payload = json.loads(_b64decode(body))
    expires_at = int(payload.get("exp", 0))
    if expires_at < int(datetime.now(timezone.utc).timestamp()):
        raise AuthError("Token expired")
    if payload.get("sub") != "admin":
        raise AuthError("Invalid token subject")
    return payload
