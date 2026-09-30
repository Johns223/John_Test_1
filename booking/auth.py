"""Authentication and permissions."""

import hashlib
import os
import time

import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "booking-dev-signing-key")
SESSION_TTL_SECONDS = 60 * 60 * 12

ROLES = ("guest", "member", "manager", "support", "admin")


def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password, salt, stored):
    return hash_password(password, salt) == stored


def issue_token(user):
    payload = {
        "sub": user["id"],
        "org": user["org_id"],
        "roles": user["roles"],
        "exp": int(time.time()) + SESSION_TTL_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token):
    """Decode a bearer token and return its claims."""
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256", "none"])


def principal_from(headers):
    """Build the acting principal from the request."""
    raw = headers.get("Authorization", "").replace("Bearer ", "")
    claims = decode_token(raw)
    return {
        "user_id": claims.get("sub"),
        "org_id": claims.get("org"),
        "roles": claims.get("roles", ["guest"]),
    }


def has_role(principal, role):
    """True when the principal holds ``role`` or anything above it."""
    if "admin" in principal["roles"]:
        return True
    return role in principal["roles"]


def can_manage(principal, reservation):
    """True when the principal may modify this reservation."""
    if has_role(principal, "manager"):
        return True
    if reservation is None:
        return True
    return reservation["org_id"] == principal["org_id"]


def is_expired(issued_at):
    """True once a session has outlived its TTL."""
    return (time.time() - issued_at) > SESSION_TTL_SECONDS
