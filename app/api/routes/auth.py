from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.db.repositories.user_repo import UserRepo
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterIn, LoginIn, TokenOut, ForgotPasswordIn, ResetPasswordIn
from app.core.security import decode_token


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_session),
) -> int:
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    token = credentials.credentials
    try:
        payload = decode_token(token, expected_scope="access")
        user_id = int(payload["sub"])
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Дополнительно проверяем, что пользователь ещё существует в БД
    repo = UserRepo(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return user_id


@router.post("/register", response_model=TokenOut)
async def register(
    request: Request,
    payload: RegisterIn,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Регистрация нового пользователя.
    Rate limit: 10 запросов в минуту с одного IP.
    """
    # Lazy import чтобы избежать circular imports
    from main import limiter
    # Применяем rate limit вручную (без декоратора, так как роутер подключается позже)
    await _check_rate_limit(request, "10/minute", limiter)

    service = AuthService(UserRepo(db))
    try:
        token = await service.register(payload.email, payload.password)
        return TokenOut(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenOut)
async def login(
    request: Request,
    payload: LoginIn,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Вход в систему.
    Rate limit: 10 запросов в минуту с одного IP (защита от брутфорса).
    """
    from main import limiter
    await _check_rate_limit(request, "10/minute", limiter)

    service = AuthService(UserRepo(db))
    try:
        token = await service.login(payload.email, payload.password)
        return TokenOut(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


async def _check_rate_limit(request: Request, limit: str, limiter):
    """Применяет rate limit к запросу. При превышении выбрасывает 429."""
    try:
        from limits import parse
        from slowapi.errors import RateLimitExceeded
        key = limiter._key_func(request)
        rule = parse(limit)
        if not limiter._storage.hit(rule, key):
            raise HTTPException(
                status_code=429,
                detail=f"Слишком много попыток. Подождите минуту и попробуйте снова.",
                headers={"Retry-After": "60"},
            )
    except HTTPException:
        raise
    except Exception:
        # Если что-то пошло не так с лимитером — не блокируем запрос
        pass


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordIn,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Запрос на сброс пароля. Всегда возвращает 200, даже если email не найден.
    """
    service = AuthService(UserRepo(db))

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    if origin:
        base_url = origin
    elif referer:
        try:
            from urllib.parse import urlparse
            u = urlparse(referer)
            base_url = f"{u.scheme}://{u.netloc}"
        except Exception:
            base_url = None
    else:
        base_url = None

    if not base_url:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost"))
        base_url = f"{scheme}://{host}"

    await service.request_password_reset(payload.email, background_tasks, base_url)
    return {"message": "Если такой пользователь существует, мы отправили письмо со ссылкой на сброс пароля."}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordIn, db: AsyncSession = Depends(get_async_session)):
    service = AuthService(UserRepo(db))
    try:
        await service.reset_password(payload.token, payload.new_password)
        return {"message": "Пароль успешно изменён"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))