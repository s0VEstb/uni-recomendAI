import os
import logging
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.hash import argon2

from app.core.config import settings

logger = logging.getLogger(__name__)

JWT_SECRET = settings.JWT_SECRET
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 60 * 24  # 1 день
RESET_TOKEN_EXPIRE_MIN = 60        # 1 час
ADMISSION_YEAR = 2026

# ── Startup guard: предупреждаем если используется дефолтный секрет ──
_INSECURE_SECRETS = {"CHANGE_ME", "secret", "changeme", "change_me", "test"}
if JWT_SECRET in _INSECURE_SECRETS or len(JWT_SECRET) < 32:
    logger.warning(
        "⚠️  JWT_SECRET is insecure or not set! "
        "Set a strong random JWT_SECRET in .env (min 32 chars)."
    )


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return argon2.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "scope": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def create_reset_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "scope": "password_reset",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=RESET_TOKEN_EXPIRE_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str, expected_scope: str | None = None) -> dict:
    """
    Декодирует JWT токен.

    Args:
        token: JWT строка
        expected_scope: если указан — проверяет поле scope в payload.
                        Используйте "access" для access токена,
                        "password_reset" для токена сброса пароля.

    Raises:
        ValueError: если токен невалиден, истёк или scope не совпадает.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError as e:
        raise ValueError("Invalid or expired token") from e

    if expected_scope is not None:
        token_scope = payload.get("scope")
        if token_scope != expected_scope:
            raise ValueError(
                f"Invalid token scope: expected '{expected_scope}', got '{token_scope}'"
            )

    return payload