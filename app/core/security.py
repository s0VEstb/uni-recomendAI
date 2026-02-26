from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.hash import argon2

# лучше вынести в env/config позже
JWT_SECRET = "CHANGE_ME"
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 60 * 24  # 1 день
ADMISSION_YEAR = 2026

def hash_password(password: str) -> str:
    return argon2.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return argon2.verify(password, password_hash)

def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError as e:
        raise ValueError("Invalid token") from e