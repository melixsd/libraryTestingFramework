"""
Security functions: password hashing and JWT creation/validation.
This file has no dependency on any other layer (except config) - independently testable.
"""
import bcrypt
import jwt
from datetime import timedelta
from app.core.config import settings
from app.core.time import utc_now


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    to_encode = data.copy()
    expire = utc_now() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError if the token is invalid or expired"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
