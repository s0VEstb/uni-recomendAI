from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.hash import argon2

from app.core.config import settings

ADMISSION_YEAR = 2026

# JWT параметры теперь берутся из env через settings
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 60 * 24  # 1 день


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return argon2.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iss": settings.APP_NAME,      # issuer — защита от JWT confusion
        "aud": settings.APP_NAME,      # audience
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[JWT_ALG],
            audience=settings.APP_NAME,
        )
    except JWTError as e:
        raise ValueError("Invalid token") from e