from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_async_session
from app.db.repositories.user_repo import UserRepo
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.core.security import decode_token
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
bearer_scheme = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register", response_model=TokenOut)
@limiter.limit("5/minute")  # не более 5 регистраций в минуту с одного IP
async def register(request: Request, payload: RegisterIn, db: AsyncSession = Depends(get_async_session)):
    service = AuthService(UserRepo(db))
    try:
        token = await service.register(payload.email, payload.password)
        return TokenOut(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")  # не более 10 попыток входа в минуту с одного IP
async def login(request: Request, payload: LoginIn, db: AsyncSession = Depends(get_async_session)):
    service = AuthService(UserRepo(db))
    try:
        token = await service.login(payload.email, payload.password)
        return TokenOut(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")