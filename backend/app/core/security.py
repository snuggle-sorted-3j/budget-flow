"""Security utilities for JWT authentication and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
import bcrypt
from app.core.config import settings

# Removed passlib dependency due to incompatibility with bcrypt 5.0.0+


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary containing the claims to encode in the token.
              Should include "sub" (subject) with user identifier.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The bcrypt hashed password to compare against.

    Returns:
        True if password matches, False otherwise.
    """
    # bcrypt requires bytes
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        Bcrypt hashed password string.
    """
    # bcrypt.hashpw returns bytes, we decode to str for storage
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode.

    Returns:
        Dictionary containing token payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None



