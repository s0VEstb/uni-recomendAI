from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env в os.environ (нужно для провайдеров, которые читают os.getenv)
load_dotenv(Path(__file__).resolve().parent / ".env")

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.admin import setup_admin
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging.config
from app.core.config import settings
from app.utils.logging import LOGGING_CONFIG

from app.api.routes import router as health_router


logging.config.dictConfig(LOGGING_CONFIG)


# ── Rate Limiter (shared instance, используется в роутах) ──
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ── Security Headers Middleware ──────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Добавляет заголовки безопасности на каждый ответ:
    - X-Content-Type-Options: nosniff — запрещает браузеру угадывать MIME-тип
    - X-Frame-Options: DENY — запрещает встраивание в iframe (защита от clickjacking)
    - Referrer-Policy: strict-origin-when-cross-origin — ограничивает утечку URL
    - X-XSS-Protection: 0 — отключаем устаревший XSS-фильтр (CSP его заменяет)
    - Content-Security-Policy: базовая политика для SPA
    - Permissions-Policy: ограничиваем опасные API браузера
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        # Базовый CSP: разрешаем только свои ресурсы
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https://picsum.photos; "
            "font-src 'self' https://fonts.gstatic.com; "
            "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
            "script-src 'self'; "
            "connect-src 'self';"
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Service is starting up...")
    yield
    logging.info("Service is shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
        # Скрываем docs в продакшне
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # Rate limiter state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS — только разрешённые origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    setup_admin(app)
    return app


app = create_app()
app.include_router(health_router, prefix="/api")