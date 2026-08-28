from contextlib import asynccontextmanager
import logging.config

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.admin import setup_admin
from app.core.config import settings
from app.utils.logging import LOGGING_CONFIG
from app.middlerware.security_headers import SecurityHeadersMiddleware
from app.api.routes import router as health_router


logging.config.dictConfig(LOGGING_CONFIG)

# Rate limiter — по IP-адресу
limiter = Limiter(key_func=get_remote_address)


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
        # Скрыть /docs в продакшене
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # ── Rate limiting ────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── Security Headers ─────────────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)

    # ── CORS ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:8080"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    setup_admin(app)
    return app


app = create_app()
app.include_router(health_router, prefix="/api")